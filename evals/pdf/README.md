# KT-102 — benchmark PDF tiếng Việt

Baseline `e04bfd1`; nhánh `codex/kt-102-pdf-evidence`.

Đã đo 60 lượt trên 20 PDF tiếng Việt công khai từ UNICEF, SHA-256 duy nhất.
Điều phối tiếp nhận sau khi agent hết credits, sửa phép đo RAM và đối chiếu ảnh
render để bổ sung 20 probe. Xem [manifest](sources.json) và [số đo](results.json).

- `qa` gồm 42 anchor ngắn, giữ dấu, chấm tại trang PDF vật lý (từ 1); normalize
  NFC/casefold/whitespace. Codex kiểm ảnh render, không phải nhãn người dùng độc lập.
- RAM cũ chỉ đo launcher đã được thay thế. Runner đo đỉnh tổng RSS cây tiến trình
  mỗi 10 ms và peak working set trong worker trên Windows. Shared pages có thể bị
  đếm lặp; không phải private memory. Một lượt đo lạnh, chưa có confidence interval.
- PDF, text trích đầy đủ và ảnh render ở cache/scratch ngoài Git; tải lại từ URL
  và kiểm hash. Không đưa corpus gốc hoặc bản xuất dài vào repository.

## Kết quả ngày 19/11/2026

Windows 11, Python 3.13.15. Mỗi cặp tài liệu/parser chạy subprocess riêng: 45 giây,
512 MiB, 250 trang/2 triệu ký tự. Thời gian lạnh gồm import/startup.
API: pypdf `extract_text()` mặc định, PDFium `get_text_bounded()`, PyMuPDF
`get_text('text', sort=True)`; kết quả chỉ áp dụng cho các tùy chọn này.

| Parser | Lượt thành công | Median giây | RSS lớn nhất MiB | Anchor đúng trang | Probe đúng thứ tự |
| --- | --- | --- | --- | --- | --- |
| pypdf 7.1.1 | 20/20 | 1.069 | 112.754 | 40/42 | 16/20 |
| pypdfium2 5.15.2 | 20/20 | 0.499 | 68.461 | 40/42 | 16/20 |
| PyMuPDF 2.1 | 20/20 | 0.866 | 84.500 | 40/42 | 19/20 |

Không có timeout, memory kill, U+FFFD hoặc cắt theo budget. Tuy vậy vi08 không
tìm được cả hai anchor dù ảnh đọc được; không coi text không rỗng là trích đúng.
PyMuPDF giữ thứ tự tốt hơn tại vi05/22/23. Mẫu một tổ chức, text layer, nhiều
trang đầu/mục lục: không đại diện scan/PDF hỏng. Anchor/probe chỉ đo đúng điểm đã
ghi, không phải CER/WER, độ chính xác toàn văn hoặc tái dựng cấu trúc bảng.

## License và quyết định

Đã đối chiếu nguồn chính thức ngày 19/11/2026:

- [pypdf 7.1.1](https://github.com/py-pdf/pypdf/blob/7.1.1/LICENSE): BSD 3-Clause;
  dễ triển khai và cùng kết quả anchor với PDFium trong mẫu.
- [pypdfium2/PDFium](https://pypdfium2.readthedocs.io/en/stable/readme.html#licensing):
  binding Apache-2.0/BSD-3-Clause; binary PDFium/dependencies có notices riêng cần
  giữ khi phân phối. Nhanh/ít RSS hơn ở lượt này, không cải thiện probe order.
- [PyMuPDF 2.1](https://pypi.org/project/pymupdf/2.1/) và
  [Artifex docs](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright):
  AGPLv3 hoặc thương mại. Chỉ có trong venv eval, không thêm runtime của private repo
  khi chưa quyết định license/phân phối.

**Giữ pypdf làm parser đầu tiên.** Mẫu chưa chứng minh lợi ích chất lượng đủ để
đổi parser mặc định. PDFium vẫn là renderer KT-010, đồng thời đã bổ sung fallback
text khi pypdf ném lỗi hoặc toàn bộ text rỗng; không thử bypass PDF có password.
Provenance ghi `pypdfium2-fallback`, version `light-documents-v2`, locator trang
vật lý, giữ giới hạn 200 trang/1 triệu ký tự và timeout child 45 giây của runtime.
Không phát hiện/sửa được mọi lỗi thứ tự hoặc font khi primary trả text không rỗng;
không giả rằng fallback giải quyết được vi08, không tự bật OCR.

6 test document extraction trên PostgreSQL tạm PASS, gồm fallback gọi PDFium thật
trên PDF tổng hợp, giữ file gốc/locator, encrypted không bypass, DOCX/XLSX Unicode,
ZIP lớn, idempotent DerivedContent. Toàn bộ KT-102 vẫn IN_PROGRESS vì nguồn khác
và nghiệm thu chất lượng toàn văn chưa hoàn tất; CI đúng head còn phải PASS.

## Chạy lại

Tạo venv eval riêng, cài `requirements.txt`; từ root checkout:

```powershell
python evals/pdf/run.py download --cache C:\Temp\kt-pdf-cache --output C:\Temp\unused.json
python evals/pdf/run.py measure --cache C:\Temp\kt-pdf-cache --scratch C:\Temp\kt-pdf-text --output evals/pdf/results.json
python evals/pdf/run.py score --scratch C:\Temp\kt-pdf-text --output evals/pdf/results.json
python evals/pdf/render_qa.py --cache C:\Temp\kt-pdf-cache --output C:\Temp\kt-pdf-renders
```

Đây là đường dẫn ví dụ; lượt thật dùng thư mục tạm ngoài checkout. Render mặc định
trang 4; vi05/vi17 cần trang 10 khi rà lại. Giữ hash cố định hoặc đánh dấu thay
corpus, không tự đổi manifest khi upstream thay PDF.
