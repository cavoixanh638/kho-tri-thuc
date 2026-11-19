# KT-202 — pilot có kiểm soát

Đã chạy ngày 19/11/2026 trên Windows: **8 Item, 4 Markdown/4 TXT**, bốn diễn giải
ngắn từ nguồn công khai đã kiểm HTTP/anchor và bốn fixture tự soạn có nhãn rõ.
PostgreSQL thử dùng cluster khác; thư mục Drive riêng `KIEM THU KT202` nằm dưới
root ứng dụng. Catalogue production được đọc qua kết nối read-only và so trước/
sau. OAuth chỉ bind trong bộ nhớ; database thử không có bản sao token.

[Kết quả Drive](../../docs/operations/knowledge-pilot-live-results.json): 8/8
đọc lại toàn bộ đúng SHA/version, một tệp mỗi Item. Sửa note, đổi tên Project
(hai Item), thay subtitle có version, retry, TXT/MD/TXT và thu hồi/bật lại đều
giữ ID; CaptureEvent gốc nguyên vẹn. Đây không phải thử parser PDF hay ASR.

[Kết quả connector/câu hỏi](../../docs/operations/knowledge-pilot-connector-results.json):
đọc được 8/8 trước/sau, 8/9 truy vấn đầu tìm đúng, Q5 phải rút gọn thành
`kiểm kê`. Cả 9 câu trả lời do người nghiệm thu viết có bằng chứng trong bản
đọc; phân biệt note hiện hành với lịch sử cũ và từ chối suy lời nói khi thiếu
transcript. Tìm trong folder đã biết, không phải benchmark mù hoặc bảo đảm tìm
kiếm ngữ nghĩa. Chưa mở phiên ChatGPT consumer UI độc lập, native Docs hoặc
đánh giá chất lượng trên corpus cá nhân.

## Chạy và tiếp tục

`tools/knowledge_pilot.py` cần Python backend, PostgreSQL thử đã chạy, cấu hình
Windows riêng và `KT_PILOT_PASSWORD` trong environment. CLI `--help` liệt kê
tham số. `--exercise` bắt buộc; `prepare` tạo DB mới có prefix `kt_pilot_` trên
cluster khác và folder có nhãn. Không chạy lại prepare trên DB đã tồn tại.
`update` dùng cùng target/work-dir với `private-receipt.json`, kiểm fingerprint
production và chỉ sửa các Item trong receipt. Một phase update chỉ chạy một lần.
Receipt/private connector observations nằm ngoài Git, không chứa token. Không
xóa DB/folder hoặc tệp thật để chạy lại; một lần đo mới dùng tên DB và work-dir
mới. Phục hồi sau lỗi phải xem receipt và trạng thái job trước khi ghi tiếp.

Nghiệm thu connector dùng metadata rồi fetch từng ID từ receipt qua plugin
Google Drive; chạy các truy vấn trong `pilot-cases.json`, giữ nguyên kết quả
không tìm thấy và chỉ dùng fallback đã định trước. Sau update, fetch lại cùng
ID và lưu observations riêng (`before`, `after`, `searches`, `answers`).
`tools/score_knowledge_pilot.py --observations <private.json> --report <report.json>`
chấm và xuất bản báo cáo chỉ dùng alias. Không đưa raw export/ID riêng vào Git.

Năm safety test chạy bằng `python -m unittest discover -s tools -p
test_knowledge_pilot.py -v`; đã PASS trên Windows, có bước tương ứng trong CI.
Rollback thay đổi này chỉ cần revert tools/evidence; không đổi mã ứng dụng,
schema hoặc cấu hình Windows đang phục vụ người dùng.
