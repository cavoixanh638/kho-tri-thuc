"""Reproducible bounded PDF extractor measurements; corpus/text stay outside Git."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import time
import unicodedata
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from urllib.parse import urlsplit

LIBRARIES = ("pypdf", "pypdfium2", "PyMuPDF")
MAX_BYTES = 40 * 1024 * 1024
MAX_PAGES = 250
MAX_CHARACTERS = 2_000_000
TIMEOUT = 45
MEMORY_BYTES = 512 * 1024 * 1024
HERE = Path(__file__).resolve().parent
VIETNAMESE = re.compile(r"[ĂăÂâĐđÊêÔôƠơƯư\u1ea0-\u1ef9]")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def outside_repository(path):
    path = Path(path).resolve()
    repository = HERE.parents[1]
    if path == repository or repository in path.parents:
        raise ValueError("Raw corpus, rendered pages and full text must be outside Git")
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", text).split()).casefold()


def download(manifest, cache):
    import requests

    for document in manifest["documents"]:
        path = cache / (document["sha256"] + ".pdf")
        if (
            path.exists()
            and hashlib.sha256(path.read_bytes()).hexdigest() == document["sha256"]
        ):
            continue
        parts = urlsplit(document["url"])
        if parts.scheme != "https" or parts.hostname not in {
            "www.unicef.org",
            "www.undp.org",
        }:
            raise ValueError("Only curated official corpus URLs are accepted")
        deadline = time.monotonic() + 90
        payload = bytearray()
        with requests.get(document["url"], stream=True, timeout=(15, 30)) as response:
            response.raise_for_status()
            if any(
                urlsplit(item.url).hostname not in {"www.unicef.org", "www.undp.org"}
                for item in [*response.history, response]
            ):
                raise ValueError("Unexpected corpus redirect")
            for chunk in response.iter_content(65536):
                payload.extend(chunk)
                if len(payload) > MAX_BYTES or time.monotonic() > deadline:
                    raise ValueError("Corpus download exceeded limits")
        if (
            not payload.startswith(b"%PDF")
            or hashlib.sha256(payload).hexdigest() != document["sha256"]
        ):
            raise ValueError("Corpus hash changed; review manifest before benchmarking")
        path.write_bytes(payload)
        print("downloaded", document["id"], flush=True)


def extract(library, path):
    pages = []
    if library == "pypdf":
        from pypdf import PdfReader

        document = PdfReader(path)
        if document.is_encrypted and not document.decrypt(""):
            raise ValueError("encrypted_pdf")
        count = len(document.pages)
        iterator = (
            (number, page.extract_text() or "")
            for number, page in enumerate(document.pages[:MAX_PAGES], 1)
        )
    elif library == "pypdfium2":
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(path)
        count = len(document)

        def pdfium_pages():
            for number in range(min(count, MAX_PAGES)):
                page = document[number]
                text_page = page.get_textpage()
                try:
                    yield number + 1, text_page.get_text_bounded()
                finally:
                    text_page.close()
                    page.close()

        iterator = pdfium_pages()
    else:
        import pymupdf

        document = pymupdf.open(path)
        if document.is_encrypted and not document.authenticate(""):
            raise ValueError("encrypted_pdf")
        count = len(document)
        iterator = (
            (number + 1, document[number].get_text("text", sort=True))
            for number in range(min(count, MAX_PAGES))
        )
    used = 0
    try:
        for number, text in iterator:
            text = text[: MAX_CHARACTERS - used]
            pages.append({"page": number, "text": text})
            used += len(text)
            if used >= MAX_CHARACTERS:
                break
    finally:
        if hasattr(iterator, "close"):
            iterator.close()
        if hasattr(document, "close"):
            document.close()
    return {
        "page_count": count,
        "pages": pages,
        "limited": count > len(pages) or used >= MAX_CHARACTERS,
    }


def worker(library, path, output):
    import psutil

    started = time.perf_counter()
    try:
        result = extract(library, path)
        result["status"] = "ok"
    except Exception as error:  # noqa: BLE001 - retain type only, no source content or paths
        result = {"status": "error", "error_type": type(error).__name__}
    result["extract_seconds"] = time.perf_counter() - started
    memory = psutil.Process().memory_info()
    result["worker_peak_rss_mib"] = round(
        max(memory.rss, getattr(memory, "peak_wset", 0)) / 1024 / 1024, 3
    )
    write_json(output, result)


def measure_one(library, document, cache, scratch):
    import psutil

    output = scratch / (document["id"] + "-" + library + ".json")
    output.unlink(missing_ok=True)
    path = cache / (document["sha256"] + ".pdf")
    if (
        not path.is_file()
        or hashlib.sha256(path.read_bytes()).hexdigest() != document["sha256"]
    ):
        raise ValueError("Missing/mismatched corpus input")
    started = time.perf_counter()
    peak_rss = 0
    status = None
    # Separate process per library/document. Stdout/stderr are discarded to keep reports content-free.
    with subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).resolve()),
            "worker",
            "--library",
            library,
            "--pdf",
            str(path),
            "--output",
            str(output),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    ) as process:
        monitored = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                processes = [monitored, *monitored.children(recursive=True)]
                resident = 0
                for child in processes:
                    try:
                        resident += child.memory_info().rss
                    except psutil.NoSuchProcess:
                        continue
                peak_rss = max(peak_rss, resident)
            except psutil.NoSuchProcess:
                break
            if peak_rss > MEMORY_BYTES:
                status = "memory_limit"
                break
            if time.perf_counter() - started > TIMEOUT:
                status = "timeout"
                break
            time.sleep(0.01)
        if process.poll() is None:
            for child in reversed(monitored.children(recursive=True)):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            process.kill()
        process.wait(timeout=5)
    wall = time.perf_counter() - started
    result = {
        "document_id": document["id"],
        "library": library,
        "cold_wall_seconds": round(wall, 6),
        "peak_rss_mib": round(peak_rss / 1024 / 1024, 3),
    }
    if status:
        return {**result, "status": status}
    if not output.is_file() or output.stat().st_size > 16 * 1024 * 1024:
        return {**result, "status": "child_failed"}
    extracted = read_json(output)
    if extracted["status"] != "ok":
        return {
            **result,
            "status": extracted["status"],
            "error_type": extracted["error_type"],
        }
    text = "\n".join(page["text"] for page in extracted["pages"])
    return {
        **result,
        "status": "ok",
        "worker_peak_rss_mib": extracted["worker_peak_rss_mib"],
        "extract_seconds": round(extracted["extract_seconds"], 6),
        "page_count": extracted["page_count"],
        "pages_extracted": len(extracted["pages"]),
        "limited": extracted["limited"],
        "characters": len(text),
        "vietnamese_diacritics": len(VIETNAMESE.findall(text)),
        "replacement_characters": text.count("\ufffd"),
        "empty_pages": sum(not page["text"].strip() for page in extracted["pages"]),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def score(manifest, results, scratch):
    references = {
        document["id"]: document.get("qa", []) for document in manifest["documents"]
    }
    for record in results["measurements"]:
        if record["status"] != "ok":
            continue
        pages = {
            page["page"]: normalized(page["text"])
            for page in read_json(
                scratch / (record["document_id"] + "-" + record["library"] + ".json")
            )["pages"]
        }
        anchors = order_pairs = matching = ordered = 0
        details = []
        for probe in references[record["document_id"]]:
            page = pages.get(probe["page"], "")
            positions = [page.find(normalized(anchor)) for anchor in probe["anchors"]]
            anchors += len(positions)
            matching += sum(position >= 0 for position in positions)
            in_order = all(
                first >= 0 and second > first for first, second in pairwise(positions)
            )
            if len(positions) > 1:
                order_pairs += 1
                ordered += in_order
            details.append(
                {
                    "page": probe["page"],
                    "matches": [position >= 0 for position in positions],
                    "in_order": in_order,
                }
            )
        record["qa"] = {
            "anchors": anchors,
            "matching": matching,
            "order_probes": order_pairs,
            "ordered": ordered,
            "details": details,
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["download", "measure", "score", "worker"])
    parser.add_argument("--manifest", type=Path, default=HERE / "sources.json")
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--library", choices=LIBRARIES)
    args = parser.parse_args()
    if args.action == "worker":
        worker(args.library, args.pdf, args.output)
        return
    manifest = read_json(args.manifest)
    if len({document["sha256"] for document in manifest["documents"]}) != len(
        manifest["documents"]
    ):
        raise ValueError("Duplicate corpus hash")
    if args.action == "download":
        download(manifest, outside_repository(args.cache))
    elif args.action == "measure":
        cache = outside_repository(args.cache)
        scratch = outside_repository(args.scratch)
        results = {
            "measured_at": datetime.now(UTC).isoformat(),
            "environment": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "versions": {
                    name: importlib.metadata.version(name)
                    for name in (*LIBRARIES, "psutil")
                },
            },
            "limits": {
                "memory_metric": "peak sampled aggregate process-tree RSS (10 ms); worker OS peak working set separately on Windows",
                "seconds_per_document_library": TIMEOUT,
                "memory_mib": MEMORY_BYTES // 1024 // 1024,
                "max_pages": MAX_PAGES,
                "max_characters": MAX_CHARACTERS,
            },
            "measurements": [],
        }
        for document in manifest["documents"]:
            for library in LIBRARIES:
                row = measure_one(library, document, cache, scratch)
                results["measurements"].append(row)
                write_json(args.output, results)
                print(
                    document["id"],
                    library,
                    row["status"],
                    row["cold_wall_seconds"],
                    flush=True,
                )
    else:
        write_json(
            args.output,
            score(manifest, read_json(args.output), outside_repository(args.scratch)),
        )


if __name__ == "__main__":
    main()
