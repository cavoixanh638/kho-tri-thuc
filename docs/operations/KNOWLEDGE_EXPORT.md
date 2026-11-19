# Bản xuất tri thức — pilot Windows

Mỗi Item mặc định **tắt**, chỉ bật riêng trong Chi tiết mục. Pilot giới hạn 10
Item đang bật/tài khoản. File gốc và nội dung người dùng không bị sửa. Bản xuất
chứa tiêu đề, mô tả, ghi chú, nhóm, nguồn, thông tin tệp, CaptureEvent và
DerivedContent hiện hành; video thiếu transcript có cảnh báo rõ.

## Hợp đồng API

Các endpoint dùng session/CSRF và kiểm owner, UUID của Item:

| Phương thức | Đường dẫn sau `/api/v1` | Kết quả |
| --- | --- | --- |
| GET | `/items/{id}/knowledge-export` | Bật/tắt, format, status, source/exported version, stale, truncated, lỗi an toàn, giờ sync, URL khi đã sync |
| POST | `/items/{id}/knowledge-export` | Body `{ "enabled": true, "format": "markdown" }` hoặc `text`; 409 nếu quá 10 mục hoặc bật mục đã xóa |
| POST | `/items/{id}/knowledge-export/retry` | Xếp lại job, không tạo CaptureEvent hoặc Item mới |

GET không bật hoặc xếp job ngầm. `stale` so với snapshot hiện tại kể cả khi bulk
update không phát signal. Worker tuần tự hóa ghi theo row KnowledgeExport,
kiểm lease trước/sau network, lưu file ID trước create và dùng lại khi retry.
Nếu input đổi trong lúc upload thì xếp successor để đưa cùng file tới bản mới.
Mỗi tệp có marker item, MIME, version và checksum được kiểm trước khi báo synced.

Model signals xếp job khi note/source/nhóm/DerivedContent thay đổi; worker hook
bù cho bulk updates. Tắt xuất hoặc soft-delete Item chỉ trash derivative được
đánh dấu đúng, không trash original. Khôi phục/bật lại dùng cùng file ID. Lỗi
quyền/identity không tự tạo file ID thay thế hay ghi đè file không được quản lý.

Snapshot tối đa 100.000 ký tự, tối đa 1.000 dòng mỗi collection; cắt có ghi rõ.
Thay đổi đuôi DerivedContent vẫn đổi source version qua hash DB. Heuristic phát
hiện một số chuỗi giống credential sẽ chặn body và thu hồi derivative cũ; đây
không phải công cụ khử mọi thông tin riêng tư. Người dùng cần xem nội dung trước
khi bật và chịu trách nhiệm chọn các mục muốn xuất.

## Lựa chọn định dạng

TXT đơn giản, dễ thay thế; Markdown giữ tiêu đề/locator rõ hơn. Cả hai là blob,
có thể dùng ID sinh trước và update cùng file. Google Docs native có lợi khi
connector hỗ trợ tốt nhưng **không hỗ trợ pre-generated ID** cho create/import;
muốn dùng cần thêm reconcile khi phản hồi tạo file bị mất, không blind retry.
Nguồn chính thức: [upload/ID](https://developers.google.com/workspace/drive/api/guides/manage-uploads),
[update nội dung](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update).
Chưa đưa native Docs vào runtime. Không cam kết ChatGPT đọc/index mọi format.

## Kiểm thử và triển khai

Backend pilot có 13 test snapshot/worker/API PASS trên PostgreSQL 18.4 thử riêng;
frontend có 14 JSDOM test PASS và production build PASS. Full regression Windows:
179 test, 178 PASS/1 skip FFmpeg do PATH; đã chạy riêng 11 thumbnail test với
FFmpeg rõ đường dẫn, PASS không skip. Backup v2 roundtrip/archive/compat v1 có
11 test PASS. Migration 0003/0004 xuôi/ngược/áp lại và makemigrations check PASS.
Chưa deploy phần xuất tri thức ở mốc này, chờ CI đúng head.
Browser tương tác/connector thật còn chặn bởi phiên CUA không đọc được giao diện.

Backup manifest v2 thêm `knowledge_exports`, giữ file mapping, preference và
version; vẫn xác minh/restore được manifest v1 (14 collection). OAuth/session vẫn
không đi theo dump. Sau restore phải migrate nếu schema cũ và kết nối lại OAuth;
folder ChatGPT_Index được tìm lại bằng marker, không suy folder từ tên.

KT-201/202E còn pilot 5–10 Item thật/nguồn công khai và câu hỏi kiểm đọc, so TXT/
Markdown/native Docs khi connector truy cập được. Không thêm dữ liệu giả vào
runtime production, không tự xuất toàn kho và không xây MCP để né cổng này.
