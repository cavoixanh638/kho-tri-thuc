"""Verify the normal session and capture routes through the frontend proxy."""

import json
import time
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

ORIGIN = "http://127.0.0.1:5173"
CLIENT = build_opener(HTTPCookieProcessor(CookieJar()))


def json_request(method, path, payload=None, *, csrf=None, key=None, status=200):
    headers = {"Accept": "application/json"}
    if csrf:
        headers.update({"X-CSRFToken": csrf, "Origin": ORIGIN})
    if key:
        headers["Idempotency-Key"] = key
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode()
    request = Request(f"{ORIGIN}/api/v1{path}", data, headers, method=method)
    with CLIENT.open(request, timeout=15) as response:
        if response.status != status:
            raise AssertionError(
                f"{method} {path} expected HTTP {status}, got {response.status}"
            )
        return json.load(response)


def main():
    pre_login = json_request("GET", "/session")
    signed_in = json_request(
        "POST",
        "/session",
        {"username": "kt-smoke", "password": "kt-smoke-fixture-only"},
        csrf=pre_login["csrf_token"],
    )
    assert signed_in["authenticated"]
    csrf = signed_in["csrf_token"]
    note = {"kind": "text", "text": " Ghi chú tiếng Việt\n dòng 2 "}
    key = str(uuid4())
    first = json_request("POST", "/captures", note, csrf=csrf, key=key, status=201)
    retry = json_request("POST", "/captures", note, csrf=csrf, key=key)
    assert retry == first
    detail = json_request("GET", f"/items/{first['item_id']}")
    assert detail["note"] == note["text"]
    assert detail["asset_storage"] == "not_applicable" and detail["assets"] == []
    assert detail["saved_at"] == first["received_at"]

    url = "https://smoke-fixture.invalid/reference"
    first_link = json_request(
        "POST",
        "/captures",
        {"kind": "link", "url": url, "text": "Lần đầu"},
        csrf=csrf,
        key=str(uuid4()),
        status=201,
    )
    second_link = json_request(
        "POST",
        "/captures",
        {"kind": "link", "url": url, "text": "Gửi thêm"},
        csrf=csrf,
        key=str(uuid4()),
        status=201,
    )
    assert first_link["item_id"] == second_link["item_id"]
    assert first_link["capture_id"] != second_link["capture_id"]
    history = json_request("GET", f"/items/{first_link['item_id']}/captures")
    annotations = {entry["raw_text"] for entry in history["results"]}
    assert annotations == {"Lần đầu", "Gửi thêm"}
    library = json_request("GET", "/items")
    assert len(library["results"]) == 2
    boundary = "kt-smoke-boundary"
    payload = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="fixture.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
        "Synthetic upload fixture\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    upload_key = str(uuid4())
    upload = Request(
        f"{ORIGIN}/api/v1/uploads",
        payload,
        {
            "Accept": "application/json",
            "Origin": ORIGIN,
            "X-CSRFToken": csrf,
            "Idempotency-Key": upload_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with CLIENT.open(upload, timeout=15) as response:
        assert response.status == 201
        receipt = json.load(response)
    with CLIENT.open(upload, timeout=15) as response:
        assert response.status == 200
        assert json.load(response)["asset_id"] == receipt["asset_id"]
    file_detail = json_request("GET", f"/items/{receipt['item_id']}")
    assert file_detail["assets"][0]["asset_id"] == receipt["asset_id"]
    assert file_detail["assets"][0]["status"] != "verified"
    group = json_request(
        "POST",
        "/groups",
        {"kind": "topic", "name": "Hạ tầng số"},
        csrf=csrf,
        status=201,
    )
    related_note = {
        "kind": "text",
        "text": "Hạ tầng số giúp kết nối trường học với dữ liệu dùng chung.",
    }
    one = json_request(
        "POST", "/captures", related_note, csrf=csrf, key=str(uuid4()), status=201
    )
    two = json_request(
        "POST", "/captures", related_note, csrf=csrf, key=str(uuid4()), status=201
    )
    assert one["item_id"] != two["item_id"]
    for _ in range(150):
        organization = json_request("GET", f"/items/{two['item_id']}/organization")
        related = json_request("GET", f"/items/{two['item_id']}/related")
        if organization["topics"] and related["results"]:
            break
        time.sleep(0.2)
    assert any(topic["id"] == group["id"] for topic in organization["topics"])
    assert any(hit["item_id"] == one["item_id"] for hit in related["results"])
    search = json_request("GET", "/search?q=ha%20tang%20so")
    assert {one["item_id"], two["item_id"]}.issubset(
        {hit["item_id"] for hit in search["results"]}
    )
    browse = json_request("GET", f"/search?topic_id={group['id']}")
    assert {one["item_id"], two["item_id"]}.issubset(
        {hit["item_id"] for hit in browse["results"]}
    )
    assert not json_request("DELETE", "/session", csrf=csrf)["authenticated"]
    print("Capture smoke PASS through frontend proxy")


if __name__ == "__main__":
    main()
