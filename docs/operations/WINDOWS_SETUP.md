# Chạy trên Windows

Bản native đã được cài và khởi động trên Windows này tại `http://127.0.0.1:8009` bằng Python 3.13, Node.js 24 và PostgreSQL 18.4. Mã nguồn giữ trên GitHub. Bản checkout chạy nằm ở `%LOCALAPPDATA%\KhoTriThuc\source`, dữ liệu riêng ở `%LOCALAPPDATA%\KhoTriThuc\runtime`.

## Khởi động và dừng

Từ thư mục checkout ứng dụng.

```powershell
python tools/windows/launch.py setup
python tools/windows/launch.py start
python tools/windows/launch.py status
powershell -ExecutionPolicy Bypass -File tools/windows/stop.ps1
```

`setup` cài môi trường Python riêng, build frontend, tạo cluster PostgreSQL 18 riêng trên loopback cổng 54329 và chạy migration. Lệnh cần Git/Node/Python và bộ PostgreSQL 18 tại `C:\Program Files\PostgreSQL\18\bin`. Thư mục runtime được giới hạn ACL cho tài khoản Windows đang chạy. `start` chạy Waitress và một worker ẩn. `stop.ps1` kiểm tra executable/command line trước khi dừng PID thuộc ứng dụng.

Đăng nhập ban đầu có trong `%LOCALAPPDATA%\KhoTriThuc\runtime\initial-login.txt`. Cấu hình và token nằm ngoài Git. Giữ thư mục runtime khi cập nhật mã. Cluster PostgreSQL đang mở và staging nằm ngoài Drive sync.

## Cấu hình Google Drive

Trong Google Cloud project dùng ổn định cho ứng dụng, bật Drive API, khai báo scope `drive.file`, tạo Web OAuth Client với redirect URI chính xác sau.

```text
http://127.0.0.1:8009/api/v1/integrations/drive/callback
```

Tải JSON OAuth client về máy. Gọi lệnh sau với đường dẫn thực của file, rồi dừng và khởi động lại ứng dụng.

```powershell
python tools/windows/launch.py configure-drive --client-file "C:\path\to\client.json"
```

Mở Cài đặt của ứng dụng và bấm Kết nối Google Drive. Chủ tài khoản thực hiện đăng nhập/cấp quyền. Công cụ chỉ giữ cấu hình bí mật trên máy. Khi có kết nối, các upload lỗi vì chưa cấu hình được đưa lại vào hàng đợi.

Web OAuth client thật đã được tạo, callback đã đăng ký, scope `drive.file` và tài khoản thử nghiệm đã lưu trong Google Cloud. JSON đã được nạp bằng `configure-drive`; ứng dụng đã build, migrate và khởi động lại thành công. Client secret chỉ nằm trong cấu hình riêng trên Windows.

Đăng nhập/cấp quyền Google đã hoàn tất. [Live smoke](drive-live-results.json) đã kiểm upload/verify/đọc lại byte chính xác và retry cùng file với TXT tiếng Việt, PNG, PDF qua adapter thật. Mẫu đã chuyển vào Thùng rác Drive, các bản ghi catalog thử nằm trong transaction rollback. [Reel thực](facebook-live-results.json) đã đi qua tiếp nhận UI, worker và Drive, tải lại khớp SHA-256. UI multipart với file người dùng, đổi client/project, upload lớn, Android thiết bị thật và HTTPS còn cần kiểm chứng. Bản hiện tại phục vụ loopback trên Windows.

OAuth đang ở trạng thái External/Testing. Refresh token có hạn 7 ngày khi dùng scope Drive, theo [Google OAuth](https://developers.google.com/identity/protocols/oauth2#expiration). Khi hết hạn, mở Cài đặt và Kết nối lại. Chuyển sang Production là bước riêng còn mở trước khi vận hành lâu dài.

Chạy lại bài kiểm tra từ checkout với cấu hình riêng đã cài. Báo cáo chỉ có hash, số byte và kết quả, không có ID tài khoản/file hoặc token.

```powershell
$ktRuntime = Join-Path $env:LOCALAPPDATA 'KhoTriThuc'
$ktConfig = Get-Content -LiteralPath "$ktRuntime\runtime\config.json" -Raw | ConvertFrom-Json
$ktConfig.environment.psobject.Properties | ForEach-Object {
    [Environment]::SetEnvironmentVariable($_.Name, [string]$_.Value, 'Process')
}
& "$ktRuntime\venv\Scripts\python.exe" tools/drive_smoke.py --owner admin --output "$env:TEMP\kt-drive-smoke.json"
```

## Video Facebook công khai

Worker tiếp nhận liên kết trước, rồi chạy `download_video` độc lập với lấy HTML. Downloader `yt-dlp==2026.10.26` ở tiến trình riêng có giới hạn 120 giây/128 MiB, không dùng cookie hoặc đăng nhập Facebook. Bản này hỗ trợ URL HTTPS Facebook dạng `/share/r/...`, `/reel/<số>` và `/watch?v=<số>`, chọn MP4 progressive HD/SD có cả hình và tiếng. Khi không lấy được tệp, liên kết và lịch sử tiếp nhận vẫn còn.

Trước khi tạo Asset, ffprobe xác minh MP4 có video/audio. Tệp được fsync vào staging rồi job upload sẵn có đưa lên Drive và kiểm SHA-256. Retry tái sử dụng Asset/Drive ID, không tạo CaptureEvent mới. Tải được video chưa đồng nghĩa đã có transcript hoặc đã hiểu nội dung.

Transport Drive dùng factory `googleapiclient.http.build_http()` để giao phản hồi `308 Resume Incomplete` cho bộ upload, tránh nhầm thành redirect thiếu Location. Chunk 1 MiB, timeout mỗi request 30 giây, budget upload 360 giây. [Google mô tả upload nhiều chunk và mã 308](https://developers.google.com/workspace/drive/api/guides/manage-uploads).

Công cụ `tools/verify_drive_item.py` tải streaming để đối chiếu SHA-256, kiểm file Drive duy nhất và so fingerprint CaptureEvent với mốc trước thao tác. Nạp biến môi trường runtime như phần Drive smoke ở trên. Ghi baseline trước retry, rồi chạy xác minh sau khi worker hoàn tất. File baseline chỉ có thời điểm, số lượt và fingerprint, không chứa nội dung gốc.

```powershell
$ktPython = Join-Path $env:LOCALAPPDATA 'KhoTriThuc\venv\Scripts\python.exe'
& $ktPython tools/verify_drive_item.py --owner admin --item '<UUID của mục>' --baseline "$env:TEMP\kt-capture-before.json" --record-baseline
# Thử xử lý lại mục trong ứng dụng, chờ worker hoàn tất.
& $ktPython tools/verify_drive_item.py --owner admin --item '<UUID của mục>' --baseline "$env:TEMP\kt-capture-before.json" --output "$env:TEMP\kt-drive-verified.json"
```

Trên Windows cài media tools bằng lệnh đã kiểm chứng sau, từ checkout. Script tải FFmpeg/ffprobe 9.0.2 từ Gyan, kiểm SHA-256 của gói trước khi chạy và ghi đường dẫn vào cấu hình riêng. Binary và giấy phép đi kèm nằm ngoài Git trong `%LOCALAPPDATA%\KhoTriThuc\tools`. Khởi động lại ứng dụng sau cài.

```powershell
powershell -ExecutionPolicy Bypass -File tools/windows/install_ffmpeg.ps1
```

[FFmpeg giới thiệu nhà cung cấp Windows](https://ffmpeg.org/download.html) · [Gói và checksum Gyan](https://www.gyan.dev/ffmpeg/builds/) · [yt-dlp](https://github.com/yt-dlp/yt-dlp)

## Quyết định runtime

Django và một PostgreSQL 18 giữ nguyên vai trò đã chốt. Runtime Windows dùng Waitress WSGI với 8 thread và WhiteNoise cho bản build tĩnh. Waitress hỗ trợ Windows và không yêu cầu server Node khi chạy app. Uvicorn hỗ trợ Windows qua worker spawn khi có nhu cầu ASGI. Gunicorn hướng tới Unix. Đây là lựa chọn vận hành native sau khi người dùng chọn máy Windows, Docker Compose tiếp tục là môi trường CI đã kiểm chứng.

[Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/) · [Uvicorn deployment](https://www.uvicorn.org/deployment/) · [Gunicorn](https://docs.gunicorn.org/en/stable/) · [Google OAuth Web client](https://developers.google.com/workspace/guides/create-credentials)
