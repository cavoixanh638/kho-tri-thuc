"""Local CPU latency benchmark for exact retrieval on synthetic Vietnamese notes.

Call build_index with the document encoder, then measure with the query encoder
and cross-encoder. Encoders must return normalized rows in input order.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from time import perf_counter_ns

import numpy as np

# Query paraphrases and their corresponding synthetic notes. No IDs in queries.
CASES = (
    ("Làm sao để bánh mì tự làm có vỏ giòn lâu?", "Bánh mì vỏ giòn", "Nướng mẻ bánh có khay nước ở đáy lò, bỏ khay giữa chừng và để nguội trên vỉ."),
    ("Có cách nào nhận biết cây ngoài ban công đang thừa nước?", "Chậu húng quế úng rễ", "Đất vẫn ẩm sau hai ngày, lá dưới ngả vàng. Kiểm tra lỗ thoát dưới đáy chậu."),
    ("Xe đạp phát tiếng lạch cạch khi chuyển số thì chỉnh gì?", "Căn líp xe đạp", "Xích chạm líp bên cạnh lúc lên dốc. Chỉnh ốc tăng dây đề từng nấc nhỏ."),
    ("Gói đồ thế nào cho chuyến trekking có mưa?", "Ba lô đi bộ xuyên rừng", "Bọc riêng áo khô và túi ngủ bằng túi chống nước, để áo mưa ở ngăn dễ lấy."),
    ("Khi chụp trẻ đang chạy nên chỉnh máy ảnh ra sao?", "Ảnh chuyển động bị nhòe", "Tăng tốc độ màn trập và chuyển sang lấy nét liên tục trước khi bấm máy."),
    ("Quản lý các khoản chi gia đình hay quên ghi lại bằng cách nào?", "Sổ thu chi gia đình", "Đặt lịch cuối tuần để ghi tiền mặt và rà lại từng giao dịch trên sao kê."),
    ("Nút tai nghe không dây chỉ sạc được một bên thì kiểm tra gì?", "Hộp sạc tai nghe Bluetooth", "Lau nhẹ các tiếp điểm và kiểm tra chân sạc có bị kẹt bên tai không lên pin."),
    ("Phân biệt hai bản biên bản họp gần như giống nhau thế nào?", "Biên bản họp đã duyệt", "Mở lịch sử chỉnh sửa, đối chiếu ngày duyệt và người ký trước khi gửi bản cuối."),
    ("Bé quên nhanh từ đã học, nên ôn như thế nào?", "Thẻ ghi nhớ từ mới", "Cho bé nhắc lại nghĩa trước khi lật thẻ và giãn khoảng cách giữa các lần ôn."),
    ("Pha cà phê phin bị chua gắt thì thay đổi gì?", "Cà phê chiết xuất thiếu", "Xay hạt mịn hơn một chút, dùng nước nóng hơn và ghi lại thời gian nhỏ giọt."),
    ("Vì sao ống thoát dưới bồn rửa nhỏ nước dù đã vặn chặt?", "Khớp nối xi phông rò", "Tháo khớp, kiểm tra chiều lắp và vết nứt trên gioăng rồi thử xả một chậu nước."),
    ("Để tài liệu quý khỏi mốc vào mùa nồm cần làm gì?", "Bảo quản hồ sơ giấy", "Cất hộp trên kệ thoáng, đo độ ẩm và kiểm tra dấu mốc trên bìa mỗi tuần."),
    ("Vì sao bản thu giọng nói lại vang như ở phòng trống?", "Giảm tiếng dội khi thu âm", "Kéo rèm dày, kê tấm tiêu âm sau người đọc và đưa micrô sát hơn."),
    ("Làm sao tra chuyến xe buýt cuối về nhà sau ca tối?", "Giờ xe buýt chạy cuối ngày", "Tra lịch ở bến đi theo đúng chiều về, so sánh ngày thường và cuối tuần."),
    ("Cần ghi gì trước khi đem áo dài đi sửa cho vừa?", "Phiếu sửa áo dài", "Đánh dấu chỗ cần bóp eo và ghi độ dài tay sau khi thử áo với giày."),
    ("Dùng gì để kiểm tra ảnh số có bị lỗi sau khi sao lưu?", "Kiểm tra bản sao ảnh", "Tạo mã băm trước khi chép, đối chiếu lại trên ổ dự phòng rồi mở thử vài ảnh."),
    ("Nồi dùng trên bếp điện từ thì thử tại nhà bằng gì?", "Kiểm tra đáy nồi", "Áp nam châm vào đáy. Nếu bám, thử tiếp trên vùng nấu để xem bếp nhận nồi."),
    ("Tại sao màn hình ngoài bị chớp lúc cắm máy tính xách tay?", "Màn hình rời chập chờn", "Thử cáp khác và hạ tần số quét; ghi lại độ phân giải nào tái hiện lỗi."),
    ("Muốn hạn chế thất lạc tài liệu mượn cho câu lạc bộ thì theo dõi sao?", "Sổ mượn sách câu lạc bộ", "Ghi tên người mượn, mã sách và hẹn ngày trả. Đối chiếu với kệ sau mỗi buổi."),
    ("Phát hiện lịch tưới công viên chạy sai giờ thì xem ở đâu?", "Bộ điều khiển tưới cỏ", "Đối chiếu đồng hồ hẹn giờ, cấu hình từng van và lịch chạy riêng cho cuối tuần."),
)
OBJECTS = (
    "máy hút bụi", "đồng hồ đeo tay", "máy bơm xe", "mũ bảo hiểm",
    "giá ba chân", "máy tính cầm tay", "bộ phát wifi", "máy in nhãn",
    "bút máy", "ấm đun nước", "vòi sen", "hộp đựng hồ sơ",
    "loa kéo", "thẻ đi tàu", "máy may", "ổ cứng di động",
    "chảo gang", "bàn phím điện tử", "kệ gỗ", "đèn sân vườn",
)
LOCATIONS = (
    "trong phòng sinh hoạt", "ở tầng trệt", "trong kho", "tại điểm cho mượn",
    "bên bàn làm việc", "ở phòng trực", "tại nhà văn hóa", "trên quầy",
    "ở góc thực hành", "tại nhà riêng",
)
OCCASIONS = (
    "trước buổi bàn giao", "sau đợt mưa", "khi chuẩn bị chuyển chỗ",
    "trong buổi kiểm kê", "lúc đổi ca", "vào ngày bảo dưỡng",
    "sau khi cho mượn", "trong tuần dùng thử", "trước kỳ nghỉ",
    "lúc mở cửa buổi sáng",
)
ACTIONS = (
    "Chụp lại tình trạng hiện tại và đối chiếu với ảnh tuần trước.",
    "Ghi tên người phụ trách và hẹn kiểm tra lại vào buổi sau.",
    "Thử thao tác theo hướng dẫn, ghi lại bước xảy ra trục trặc.",
    "Đánh dấu vị trí cất và đếm số phụ kiện còn trong hộp.",
    "Đọc nhật ký lần trước rồi bổ sung điều vừa quan sát được.",
)
CORPUS_SIZE = 10_000
WARMUP_REQUESTS = 3
DENSE_K = 12
LEXICAL_K = 5
RRF_K = 60


def build_corpus() -> list[str]:
    """Generate 10,000 distinct notes in stable QAJ9 token order."""
    notes = [
        f"KTJ9TERM{row:05d} {title}\n{note}"
        for row, (_, title, note) in enumerate(CASES)
    ]
    for obj in OBJECTS:
        for location in LOCATIONS:
            for occasion in OCCASIONS:
                for action in ACTIONS:
                    if len(notes) == CORPUS_SIZE:
                        return notes
                    title = f"{obj.capitalize()} {location}"
                    notes.append(f"KTJ9TERM{len(notes):05d} {title}\nKiểm tra {occasion}. {action}")
    raise AssertionError("Synthetic corpus size changed")


def _normalized_rows(values, n_rows, width=None):
    rows = np.asarray(values, dtype=np.float32)
    if rows.ndim != 2 or rows.shape[0] != n_rows or not rows.shape[1]:
        raise ValueError(f"Encoder must return {n_rows} nonempty rows")
    if width is not None and rows.shape[1] != width:
        raise ValueError(f"Expected vectors of width {width}")
    if not np.allclose(np.linalg.norm(rows, axis=1), 1, atol=1e-3, rtol=0):
        raise ValueError("Encoder must return finite normalized rows")
    return rows


def _checkpoint(path, state):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(path)


def build_index(encode_batch, dest, batch_size=64, *, model_id=None):
    """Write a float32 .npy index incrementally and return a read-only memmap.

    Use one writer per destination. Supply a stable model_id (including any
    revision and document prompt) to resume/reuse a build. Calls without a
    model_id start fresh when no finished index exists. Keep the .json
    checkpoint next to the .npy file for safe reuse.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    dest = Path(dest)
    if dest.suffix != ".npy":
        raise ValueError("dest must end in .npy")
    dest.parent.mkdir(parents=True, exist_ok=True)
    working = dest.with_suffix(".part.npy")
    checkpoint = dest.with_suffix(".json")
    notes = build_corpus()
    identity = {
        "corpus_sha256": hashlib.sha256("\0".join(notes).encode("utf-8")).hexdigest(),
        "model_id": model_id,
    }
    state = None
    if checkpoint.exists() and (model_id is not None or dest.exists()):
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        if model_id is None or any(state[key] != value for key, value in identity.items()):
            raise ValueError("Index identity differs; choose a new destination")
    if dest.exists():
        if state is None or state["next_row"] != len(notes):
            raise ValueError("Finished index lacks a matching completed checkpoint")
        return _open_index(dest, state, mode="r")
    first_batch = None
    if state is None:
        stop = min(batch_size, len(notes))
        first_batch = _normalized_rows(encode_batch(notes[:stop]), stop)
        state = {**identity, "next_row": 0, "width": first_batch.shape[1]}
        index = np.lib.format.open_memmap(
            working, mode="w+", dtype=np.float32, shape=(len(notes), state["width"])
        )
        _checkpoint(checkpoint, state)
    else:
        index = _open_index(working, state, mode="r+")
    try:
        for start in range(state["next_row"], len(notes), batch_size):
            stop = min(start + batch_size, len(notes))
            rows = first_batch
            if rows is None:
                rows = _normalized_rows(encode_batch(notes[start:stop]), stop - start, index.shape[1])
            index[start:stop] = rows
            index.flush()
            state["next_row"] = stop
            _checkpoint(checkpoint, state)
            first_batch = None
    finally:
        # Close the mapping before renaming the file on Windows.
        del index
    working.replace(dest)
    return _open_index(dest, state, mode="r")


def _open_index(path, state, mode):
    index = np.load(path, mmap_mode=mode, allow_pickle=False)
    if index.shape != (CORPUS_SIZE, state["width"]) or index.dtype != np.float32:
        raise ValueError("Index shape or dtype differs from checkpoint")
    return index


def _top_k(scores, k):
    cutoff = np.partition(scores, len(scores) - k)[-k]
    higher = np.flatnonzero(scores > cutoff)
    tied = np.flatnonzero(scores == cutoff)[: k - len(higher)]
    selected = np.concatenate((higher, tied))
    return selected[np.lexsort((selected, -scores[selected]))]


def _distribution(values):
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min_ms": ordered[0],
        "p50_ms": ordered[math.ceil(0.50 * len(ordered)) - 1],
        "p95_ms": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "max_ms": ordered[-1],
    }


def _rank(order, expected):
    matches = np.flatnonzero(order == expected)
    return int(matches[0]) + 1 if matches.size else None


def _fuse(dense, lexical, k):
    scores = {}
    for ranking in (dense, lexical):
        for rank, row in enumerate(ranking, start=1):
            scores[row] = scores.get(row, 0.0) + 1 / (RRF_K + rank)
    return np.array(sorted(scores, key=lambda row: (-scores[row], row))[:k])


def measure(index, encode_batch, rerank, samples=20, *, candidate_k=8, lexical=None):
    """Measure serial, warm requests including fresh encoding on every request.

    The optional lexical(query) returns up to five distinct 0-based row
    indices in lexical rank order. Its work is timed on the request path.
    """
    notes = build_corpus()
    if index.ndim != 2 or index.shape[0] != len(notes) or index.shape[1] < 1:
        raise ValueError(f"Expected an index of {len(notes)} corpus rows")
    if index.dtype != np.float32 or not np.isfinite(index).all():
        raise ValueError("Expected finite float32 document vectors")
    dense_k = DENSE_K if lexical is not None else candidate_k
    if samples < len(CASES) or not 1 <= candidate_k <= dense_k <= len(notes):
        raise ValueError(f"Use at least {len(CASES)} samples and a valid candidate_k")

    def request(case_id, *, verify=False):
        query, _, _ = CASES[case_id]
        start = perf_counter_ns()
        sparse = []
        if lexical is not None:
            sparse = list(lexical(query))
            if (
                len(sparse) > LEXICAL_K
                or any(
                    not isinstance(row, (int, np.integer)) or not 0 <= row < len(notes)
                    for row in sparse
                )
                or len(set(sparse)) != len(sparse)
            ):
                raise ValueError("Lexical results must be up to five distinct corpus row indices")
        lexical_finished = perf_counter_ns()

        vector = _normalized_rows(encode_batch([query]), 1, index.shape[1])[0]
        encoded = perf_counter_ns()
        scores = index @ vector
        dense = _top_k(scores, dense_k)
        scanned = perf_counter_ns()
        candidates = dense if lexical is None else _fuse(dense, sparse, candidate_k)
        fused = perf_counter_ns()
        documents = [notes[i] for i in candidates]
        gathered = perf_counter_ns()
        raw_scores = np.asarray(rerank(query, documents))
        if raw_scores.shape != (candidate_k,) or not np.isfinite(raw_scores).all():
            raise ValueError("Reranker must return one finite score per candidate")
        ranked = candidates[np.lexsort((candidates, -raw_scores))]
        finished = perf_counter_ns()

        if verify:
            ids = np.arange(len(scores))
            reference = np.lexsort((ids, -scores))[:dense_k]
            if not np.array_equal(reference, dense):
                raise AssertionError("Exact top-k differs from full reference sort")
        durations = {
            "query_embedding": (encoded - lexical_finished) / 1e6,
            "exact_scan_top_k": (scanned - encoded) / 1e6,
            "rerank": (finished - gathered) / 1e6,
            "online_overhead": (gathered - fused) / 1e6,
            "total": (finished - start) / 1e6,
        }
        if lexical is not None:
            durations.update(
                lexical=(lexical_finished - start) / 1e6,
                rrf_fusion=(fused - scanned) / 1e6,
                hybrid=(fused - lexical_finished) / 1e6,
                lexical_and_hybrid=(fused - start) / 1e6,
                pipeline=durations["total"],
            )
        return durations, candidates, ranked

    for n in range(WARMUP_REQUESTS):
        request(n * 7, verify=True)

    durations = []
    repetitions = Counter()
    outcomes = []
    for n in range(samples):
        case_id = n % len(CASES)
        repetitions[case_id] += 1
        ms, candidates, ranked = request(case_id)
        durations.append(ms)
        outcomes.append(
            {
                "query": CASES[case_id][0],
                "expected_note": f"KTJ9TERM{case_id:05d}",
                "expected_candidate_rank": _rank(candidates, case_id),
                "expected_reranked_rank": _rank(ranked, case_id),
            }
        )
    return {
        "scope": "local retrieval and reranking on synthetic Vietnamese notes",
        "mode": "vector-only" if lexical is None else "hybrid-with-lexical-callback",
        "dense_k": dense_k,
        "lexical_k": LEXICAL_K if lexical is not None else None,
        "rrf_k": RRF_K if lexical is not None else None,
        "index_rows": int(index.shape[0]),
        "index_dimension": int(index.shape[1]),
        "index_dtype": str(index.dtype),
        "index_vector_bytes": int(index.nbytes),
        "query_batch_size": 1,
        "candidate_k": candidate_k,
        "warmup_requests": WARMUP_REQUESTS,
        "reference_top_k_checks": WARMUP_REQUESTS,
        "measured_requests": samples,
        "requests_per_query": {CASES[k][0]: count for k, count in repetitions.items()},
        "percentiles": "nearest rank",
        "latency": {
            field: _distribution([sample[field] for sample in durations])
            for field in durations[0]
        },
        "retrieval_outcomes": outcomes,
    }
