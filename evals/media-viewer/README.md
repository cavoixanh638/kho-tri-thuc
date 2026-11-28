# Đọc PDF và MP4 trên Google Drive từ bản Windows

Ngày 25/11/2026, bộ thử tạo PDF ba trang đỏ, xanh lục, xanh dương và một MP4 H.264 dài 12 giây. Mỗi lần chạy dùng PostgreSQL tạm riêng và thư mục Drive mới, có dấu nhận diện của phép thử. Tệp PDF cỡ vừa có thêm một tệp đính kèm để đạt 5.244.465 byte. Cả ba lượt đã chuyển thư mục Drive của phép thử vào Thùng rác. Báo cáo chỉ lưu kết quả, số byte và hash mã đã chạy.

| Lần chạy trên Drive thật | Ba lần mở trang của PDF cỡ vừa | Thời gian từng trang |
| --- | --- | --- |
| [Trước khi sửa nhận diện phiên bản](drive-before.json) | Trang đầu trả HTTP 409 dù Drive trả đúng đoạn byte | Dừng ca này ở trang đầu |
| [Sau khi sửa nhận diện phiên bản](drive-revision-fix.json) | 5.244.465 / 5.244.465 / 5.244.465 byte | 4,67 / 5,11 / 5,22 giây |
| [Thêm bộ nhớ tạm và kiểm quyền từng lượt](drive-cache.json) | 5.244.465 / 1 / 1 byte | 12,10 / 2,55 / 2,95 giây |

Ở lần cuối, màu thực của cả ba trang khớp với dữ liệu gốc cho cả hai PDF trong giới hạn. Lần mở trang đầu xác minh SHA-256 toàn bộ PDF. Hai lần sau đều thực hiện một yêu cầu tải một byte qua Drive, có kiểm nguồn và quyền, trước khi dùng lại bản đã xác minh. Số byte ở bảng là dữ liệu tệp đến adapter, chưa tính metadata và HTTP headers. Mẫu có một lượt cho mỗi cấu hình và tốc độ mạng thay đổi. Tổng thời gian ba trang ở hai lần thành công lần lượt là 14,99 và 17,60 giây.

PDF 25 MiB trả 413 trước khi đọc dữ liệu nguồn. Với MP4, hai đoạn thử trả HTTP 206, khớp từng byte và Content-Range. Chromium mở được video qua Django và định vị đúng 2,5 và 9,5 giây. Mỗi tệp được kiểm với người dùng khác và với URL mang phiên bản cũ. Hai trường hợp đều bị từ chối trước khi đọc Drive. Các tệp là dữ liệu tự sinh, không có tài liệu cá nhân trong bộ thử.

Mã phục vụ ở lần cuối nằm tại commit `376d51d5bf78404b5f22c042c555b059225bd92a`. 30 kiểm thử Django dành cho private viewer, PDF và Range trên PostgreSQL QA đã đạt, gồm hủy quyền, nguồn đổi, lỗi kết nối, checksum sai, hết hạn và giới hạn lưu trong RAM. Đọc thêm [mã bộ thử](../../tools/smoke/windows_media_probe.py) và [phép seek Chromium](../../tools/smoke/windows_media_seek.mjs).

Chạy từ thư mục repo. Cần Python của backend, PostgreSQL 18, FFmpeg và Chromium. Mặc định lưu byte mẫu trong RAM. Để kiểm Drive qua ứng dụng, chỉ rõ tài khoản đã kết nối và cấu hình runtime. Bộ thử chỉ đọc cấu hình và bản ghi kết nối của tài khoản đó. Không đưa các giá trị này vào Git hoặc báo cáo.

```powershell
& $backendPython tools/smoke/windows_media_probe.py --pg-bin $pgBin --ffmpeg $ffmpeg --chrome $chrome --output $report
& $backendPython tools/smoke/windows_media_probe.py --mode drive --source-owner $qaOwner --runtime-config $runtimeConfig --pg-bin $pgBin --ffmpeg $ffmpeg --chrome $chrome --output $driveReport
```
