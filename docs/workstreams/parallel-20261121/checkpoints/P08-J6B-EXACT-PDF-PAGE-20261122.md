# KT128/J6B — định vị PDF đúng trang từ tệp nguồn đã xác minh (22/11/2026)

## Vấn đề
- Viewer hiện trả `pageNavigationVerified=false` vì iframe PDF `#page=N` không chứng minh trình duyệt đã thật sự hiển thị trang N.
- Khi người dùng cần kiểm tra trích dẫn PDF, ứng dụng phải cho xem **chính xác trang từ phiên bản nguồn được khóa bằng SHA256**, không nhảy theo metadata không kiểm chứng.

## Giải pháp nhỏ, không thêm dependency
1. `storage.pdf_page_render`: tận dụng **pypdfium2/Pillow đang cài sẵn**. Gọi child process cho đúng số trang (1-based), giới hạn PDF 12 MiB, số trang yêu cầu 1–500, ảnh tối đa 1600px/4MP/3 MiB; timeout 12 giây; chỉ output WebP hoặc mã lỗi chung, không log nội dung PDF.
2. `/api/v1/assets/{asset_id}/pdf-page/{version}/{sha256}/{page}`: chỉ user sở hữu Item, Asset có StorageLocation VERIFIED. Bóc tệp nguyên bản qua các byte-range 4 MiB `storage_for_owner.read_range`, kiểm SHA256 toàn bộ trước khi dựng ảnh, chống tráo source/version, `Cache-Control: private, no-store` và `Content-Disposition: inline`. Không trả Drive ID, token hay signed URL.
3. `/assets/{id}/viewer`: giữ `pageNavigationVerified=false` cho native iframe. Chỉ công bố năng lực `pdfPageRenderer='server_pdfium2'` với PDF đã xác minh, file trong giới hạn. Định vị được xác nhận **sau khi ảnh đúng trang tải thành công**, không dựa trên iframe/fragment.
4. Frontend React `SourceLocatorPdf`: tạo URL same-origin từ asset ID/version/SHA256/page. Hiện số trang đã yêu cầu; sau khi ảnh tải có `data-verified-page=N`. Nếu lỗi, thu hồi trạng thái và hiển thị cảnh báo, không để chứng cứ giả. Giữ fallback iframe cũ đối với legacy viewer đã được kiểm riêng.

## Kiểm thử bắt buộc
- Tạo **PDF hai trang có hai màu khác nhau** qua pypdf low-level (không sử dụng tài liệu người dùng). Chứng minh page 1 màu đỏ và page 2 màu xanh trên ảnh WebP thực sự.
- Django HTTP authenticated: đúng owner 200, trang 1/2 khác nội dung, `X-Rendered-Pdf-Page` khớp, version nguồn khớp; owner khác 404, guest 401, hash sai 409, page 0/501 422, PDF lớn 413, byte nguồn đã đổi 409.
- React DOM: nút mở viewer private, URL image pin đúng, không dùng PDF `iframe`, chỉ đánh dấu `data-verified-page` sau sự kiện tải; lỗi khôi phục trạng thái NOT_SUPPORTED.

## Giới hạn
- Đây là xem trang ảnh chính xác, không phải toàn bộ PDF trình chiếu/trích lục; file lớn hơn 12 MiB cần mở nguồn gốc hoặc phát triển cơ chế render qua streaming/cache. Không hỗ trợ PDF có mật khẩu hoặc bất khả dụng.
- Chưa có thực chứng với **Google Drive thật** hoặc 100 GB video. Không mở quyền Drive mới, không đụng production và không gọi Gemini.
- PR này là lớp tính năng mới. Cần xác nhận backend unit/frontend CI và nếu muốn đóng J6B, phải chạy **browser E2E trên chính trang PDF/MP4 tổng hợp qua endpoint backend private**. Không tự chuyển J6B PASS chỉ vì unit test đạt.

## Rollback
Không migration; đóng PR/revert file mới và thay đổi `viewer_api.py`, `SourceLocator.tsx/.css`, test. Mọi token dữ liệu và tệp nguồn được giữ ở nơi sở hữu, không lưu trong repository.
