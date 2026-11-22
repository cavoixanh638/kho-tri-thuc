# P08/J6B native media preflight — 22/11/2026

## Bối cảnh
- P08/KT128 J6B còn NOT_RUN: cần chứng minh PDF nhảy đến trang thật và MP4 nhảy đến giây thật trên file private verified. Các test P07 hiện xác minh Range 206, MIME, ETag, cross-owner và phiên bản, nhưng không phải bằng chứng trình duyệt hiển thị đúng trang PDF.
- Tránh gắn PASS cho giao diện chỉ chứa `iframe#page=2`: fragment không đồng nghĩa trình xem PDF đã di chuyển đúng trang.

## Phép thử bổ sung
- `tools/smoke/p08_j6b_native_preflight.mjs` dùng `ffmpeg` tạo MP4 12 giây 320x180 H.264, và tạo PDF 3 trang với nhãn trang khác nhau. Tính SHA256 của cả hai tệp.
- Chạy Chromium thật trên server HTTP loopback; PDF có fragment `#page=2` và được trình duyệt yêu cầu qua HTTP. Tại 4 mốc 0.5, 2.5, 6.25, 9.5 giây: đợi `seeked`, đọc `video.currentTime`, sai số cho phép 0.25 giây, xác nhận khung hình 320x180. Chụp screenshot để kiểm thủ công vị trí trang PDF.
- Giữ báo cáo `tmp/p08-j6b-native/results.json`, screenshot qua artifact Actions. Không truy cập mạng ngoài, không token Google Drive, không động tới dữ liệu thật.
- Kết quả `PREFLIGHT_PASS_NATIVE_MP4_PDF_FRAGMENT_ONLY` **chỉ** khi chạy thành công. `J6B` trong ledger tổng tiếp tục `NOT_RUN`. Không mượn preflight để vượt cổng release.

## Những phần còn thiếu cho J6B chính thức
1. Xác nhận **trang hiển thị thực sự** trong Chrome PDF viewer, không chỉ kiểm string fragment hoặc HTTP 206; phải có phương pháp kiểm trang 2 độc lập, ảnh trang chuẩn để đối chiếu.
2. Đường truyền đúng hệ thống: Item/Asset/DerivedContent nguồn private đã xác thực, phiên bản SHA256 pinned, Django owner auth và byte-range từ adapter verified. Local synthetic server chưa chứng minh yêu cầu này.
3. Đối chiếu kết quả video gắn với trích dẫn thật, mốc nhận dạng rõ ràng, không chỉ chuyển `currentTime` của video tự tạo. Phải kiểm source version, source locator.
4. Android native, Google Drive thật, giới hạn dữ liệu và tình huống provider timeout đều chưa kiểm.

## Phạm vi & rollback
Tái sử dụng runner `browser_acceptance` có sẵn; timeout bước 3 phút; không thêm job hay mở network. Có thể revert 2 file test/CI; không sửa runtime hay migration. Không merge/deploy trước nghiệm thu.
