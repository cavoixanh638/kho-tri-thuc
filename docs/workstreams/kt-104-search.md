# KT-104 — SearchService

- Baseline `c51d39f3d3719a03760944145e9cf22b15c30cc6` từ `codex/kt-003-005-drive`. Mã SearchService và migration ở `d6ffe35fa4bb7cf4275a2fa0eeb64d252dac6c0f`, test theo chế độ đăng ký app ở `0f5e4c3c5c3bf03b52e03afe613b4e9828eda168`.
- Phạm vi gồm `apps/backend/search/**` và checkpoint này. PostgreSQL dùng `public.kt_vi` với `simple`/unaccent, hai GIN FTS theo bảng và một GIN pg_trgm riêng cho metadata Item. FTS dùng `to_tsvector` và `plainto_tsquery` với cùng cấu hình. Một truy vấn gộp theo Item và giữ kết quả tốt nhất của mỗi nguồn.
- Đăng ký `search` trong `INSTALLED_APPS` và chạy migration `search.0001_search_indexes`. Các app phụ thuộc là `catalog`, `ingestion` và `processing`. Role migration cần quyền tạo extension trong DB hoặc hai extension đã được cấp sẵn ở schema `public`.
- Gọi `search.services.SearchService().search(filters, query, cursor=None, *, limit=20)` với `SearchFilters(owner_id, topic_id=None, project_id=None, tag_id=None, exclude_item_id=None)`. Lấy owner từ người dùng đã xác thực. Kết quả `SearchPage.hits` có `item_id`, `title`, `score` và `evidence` với snippet dạng văn bản, locator và provenance. Dùng lại `next_cursor` với cùng query và phạm vi. Bước tích hợp làm đăng ký app chung và nối API.
- Giới hạn hiện tại là 300 ký tự truy vấn, tối đa 100 Item mỗi trang, 40.000 ký tự đầu của từng trường description/note và 80.000 ký tự đầu của mỗi bản trích/chú thích. Truy vấn lịch sử xét tối đa 1.000 CaptureEvent loại link có chú thích mới nhất trong phạm vi. Fallback substring/typo chạy trên metadata Item. Bản trích dài cần được lưu theo đoạn/trang để tìm toàn văn.

## Kiểm chứng

PostgreSQL 18.4 UTF-8 và Django 5.2.19 trên Windows. Dùng bộ dữ liệu tổng hợp cùng settings tạm kế thừa `config.settings` và thêm `search`.

- **PASS** `python manage.py check` và `python manage.py makemigrations --check --dry-run`.
- **PASS** `python manage.py migrate --noinput`, `python manage.py migrate search zero --noinput`, xác nhận cấu hình, ba chỉ mục và ba hàm KT-104 đã bị gỡ qua catalog PostgreSQL, rồi `python manage.py migrate search --noinput`. Rollback giữ hai extension dùng chung.
- **PASS** `python manage.py test search --verbosity 2` (9/9) và `python manage.py test --noinput` (28/28). Test bao phủ tiếng Việt NFC/NFD và đ/Đ, số hiệu và lỗi gõ, thay đổi title/note/text, active/stale/failed, quyền owner/nhóm/xóa mềm, thông tin nguồn và phân trang.
- **PASS** `EXPLAIN (ANALYZE, BUFFERS)` của chính SQL SearchService. Truy vấn từ khóa dùng `kt_item_fts_gin` và `kt_derived_fts_gin`, truy vấn một phần số hiệu dùng `kt_item_trgm_gin`. Fixture gồm 4.001 Item và 4.001 bản trích, với pending list của GIN đã dọn và thống kê cập nhật bằng `ANALYZE`.
- **PASS** `python manage.py test --noinput --settings=config.settings` với settings gốc tại baseline (19 pass, 9 skip). Bộ test search tự chạy sau khi đăng ký app.
- **NOT_RUN** tích hợp endpoint HTTP và đo độ trễ trên dữ liệu thật. Bước tiếp theo ở nhánh điều phối là đăng ký app, nối API và chạy lại bộ kiểm thử với settings tích hợp.
