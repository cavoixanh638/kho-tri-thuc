# KT-102 — checkpoint chưa nghiệm thu

Baseline `e04bfd1`; nhánh `codex/kt-102-pdf-evidence`.

Đã thu manifest 20 PDF tiếng Việt công khai từ UNICEF, SHA-256 duy nhất,
runner ba thư viện và số đo sơ bộ trong `results.json`. Agent dừng do workspace
hết credits trước khi bàn giao. **IN_PROGRESS, không phải quyết định chọn parser.**

- `qa` trong manifest còn rỗng: chưa có gold anchor, thứ tự đọc hoặc đối chiếu
  locator được nghiệm thu; không suy độ chính xác từ số ký tự có dấu.
- **Số RAM sơ bộ chưa đáng tin:** cần xác nhận Windows venv launcher/tiến trình
  con thực tế được đo, rồi chạy lại. Chưa dùng số RAM để so sánh thư viện.
- Cần rà giấy phép chính thức từng phiên bản, đặc biệt PyMuPDF; phụ thuộc trong
  requirements chỉ dành cho môi trường đánh giá riêng, không thêm runtime.
- PDF, text trích đầy đủ và ảnh render ở cache/scratch ngoài Git; tải lại từ URL
  và kiểm hash. Không đưa corpus gốc hoặc bản xuất dài vào repository.

Tiếp tục: tạo venv eval riêng, đọc runner, xác minh monitor process tree, đo lại;
render trang ngoài Git và tạo anchor ngắn được kiểm bằng mắt; tổng hợp giới hạn,
license và quyết định. `run.py --help` và `render_qa.py --help` mô tả đầu vào.
Chưa chốt KT-102; production vẫn dùng pypdf baseline.
