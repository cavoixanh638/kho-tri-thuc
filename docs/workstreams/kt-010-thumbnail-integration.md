# KT-010 · Nối thumbnail vào upload và thư viện

- Nhánh `codex/kt-010-thumbnail-integration` từ candidate `f8ceec9915b239a7423041d9014c3b02ea805b50` cùng renderer `728a0786783848b08373f474260f45c344c501c8`. SHA code đã thử `db1d56322b621931569489bd60ed6c7ee168182a`.
- Root đăng ký `processing.thumbnail_api.router` ở gốc Ninja `/api/v1`, đặt `THUMBNAIL_CACHE_DIR` vào volume riêng cùng API/worker, cài requirements Pillow/pypdfium2 của renderer. Chỉ chủ sở hữu Asset có mapping Drive verified, Item chưa xóa, mới đọc được `GET /assets/{asset_id}/thumbnail`. Trả `private, no-store`. Khi chưa có thumbnail trả 404.
- Hook `thumbnail_from_staging(asset, path)` chạy sau khi upload verified và trước dọn staging. Placeholder hoặc lỗi render đã dự kiến không làm hỏng upload đã xác minh.
- `rebuild_thumbnail(asset_id, owner_id=...)` có thể gọi thủ công/worker sau khi mất cache. Chỉ dùng OAuth hiện tại và mapping đã xác minh. Tải tối đa 32 MiB theo size đã ghi và xác minh SHA-256 chính xác trước decode. Không tải tự động từ GET và chưa đăng ký scheduler/job cho helper.
- PostgreSQL 18.4 tạm trên Windows, 67/68 PASS, 1 SKIP ca video dùng FFmpeg thật vì binary không có trên máy thử. 5 ca tích hợp mới đều qua gồm cache phát sinh trước dọn staging, quyền sở hữu và HTTP headers, bỏ qua lỗi render, khôi phục cache, chặn thiếu integrity. Kiểm tra migration và Ruff đều qua.
- Drive thật, compose cache volume trên bản tổng hợp và smoke FFmpeg thật vẫn cần kiểm thử sau khi root nối runtime. Không có migration mới. Revert commit wiring giữ các bản gốc; cache có thể tạo lại.
