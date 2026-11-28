# Pilot tìm và đọc ghi chú tiếng Việt trên Windows

Mở [pilot trên máy này](http://127.0.0.1:62310) và đăng nhập bằng thông tin trong `%TEMP%\ktt-rc25-qa\pilot-login.txt`. Trong **Thư viện → Tất cả bài tri thức**, có thể mở cả 36 ghi chú. Dùng **Tìm kiếm** để thử truy vấn từ trí nhớ hoặc từ khóa không dấu. Để sửa chủ đề của một ghi chú, mở **Cấu trúc bài → Chuyển thư mục / thêm lối tắt**, chọn thư mục rồi thêm vào nhánh hoặc bỏ khỏi nhánh đã chọn. Các ghi chú và chủ đề trong tài khoản này được soạn riêng cho QA.

## Mở lại pilot sau khi khởi động Windows

Mở PowerShell tại gốc repo và chạy [trình khởi động pilot](../../tools/windows/start_synthetic_pilot.py). Cần PostgreSQL 18, Node 24, các dependency web đã cài bằng `npm ci` và venv backend có Waitress. Cần giữ thư mục `ktt-rc25-qa` với cluster `pgdata` và ba tệp `qa-password`, `pilot-login.txt`, `pilot-seed-map.json` ở ngoài Git.

```powershell
python tools/windows/start_synthetic_pilot.py
```

Trình khởi động dùng PostgreSQL QA `kt_p08_journeys` tại `127.0.0.1:56325`, kiểm tra schema hiện có, build web vào thư mục QA và phục vụ tại `127.0.0.1:62310`. Nếu cổng web đang được dùng, trình khởi động dừng trước khi build. Giữ cửa sổ PowerShell mở khi sử dụng pilot. `Ctrl+C` dừng web pilot. Nếu chạy từ sandbox hoặc dùng đường dẫn riêng, truyền `--state '<đường dẫn đến ktt-rc25-qa>'` và `--python '<đường dẫn đến python.exe trong venv backend>'`. Mặc định venv nằm dưới `%LOCALAPPDATA%\KhoTriThuc\venv`.

## Đo lại pilot hiện có

Khi pilot đang chạy, dùng PowerShell thứ hai tại gốc repo. Có thể truyền `--state` và `--chromium` nếu cần chọn thư mục QA hoặc Chrome/Chromium khác mặc định.

```powershell
python tools/windows/start_synthetic_pilot.py --measure
```

Để giữ lại báo cáo của phiên bản trước, đặt `$env:KT_EVAL_BROWSER_REPORT` thành đường dẫn JSON mới trước khi chạy. Mỗi truy vấn được gửi một lần từ ô tìm kiếm. Nếu bài đích vắng khỏi năm kết quả đầu hoặc câu hỏi không có bài phù hợp, Chromium bấm **Tìm gần đúng** khi giao diện đưa ra lựa chọn này. `summary` ghi kết quả lượt đầu, `including_expansion` ghi kết quả sau bước tùy chọn, và `expansion_clicks` đếm số lượt thực sự bấm. `ui_match_kind` ghi `partial` khi màn hình có nhãn **Ghi chú khớp một phần từ khóa**. Bộ đo kiểm tra nhãn hiển thị và liên kết với danh sách cho trình đọc màn hình.

Để kiểm tra điều hướng riêng, chạy lệnh dưới đây trên pilot đang mở. Chromium nhập câu tìm M02 và M14 qua ô tìm kiếm, chọn mục lục “thu âm” bằng bàn phím, bấm tìm, mở bài rồi quay lại và tiến tới trong lịch sử trình duyệt. Mỗi bước so khớp câu hỏi, mục lục, chế độ mở rộng trong URL và trạng thái hiển thị. Lượt mở bài còn so địa chỉ, tiêu đề và nguyên văn ghi chú. Có thể dùng cùng biến `KT_EVAL_BROWSER_REPORT` để chọn nơi lưu JSON.

```powershell
python tools/windows/start_synthetic_pilot.py --measure-navigation
```

Ngày 26/11/2026, Chrome 158 trên Windows đạt 16/16 bước ở mã ứng dụng `ba1e751`. Lượt mở rộng tìm thấy M02, bộ lọc “thu âm” loại M02 và M14 khỏi hai câu tìm đó. Bỏ bộ lọc đưa M14 trở lại. Các lần mở qua kết quả và qua lịch sử đều hiện đúng nguyên văn bài cần đọc. [Kết quả điều hướng từng bước](results-browser-navigation-20261126.json)

Phép đo đọc mật khẩu đăng nhập từ tệp riêng và kiểm tra `thu âm` vẫn vắng mặt trên M14. Kết quả `VERIFIED_ABSENT` xác nhận trạng thái của lần đo đó. Nếu cần tái hiện thao tác gỡ trên một bộ mẫu mới, đặt `KT_EVAL_BROWSER_CORRECTION=1` khi gọi trực tiếp `measure_browser.mjs`. Runner sẽ thử gỡ từ menu **Thao tác** trong cây thư mục và lưu sửa đổi đó.

Để tạo bộ mẫu mới với Django đã trỏ đúng DB QA, đặt `KT_EVAL_BROWSER_QA=1`, `KT_EVAL_BROWSER_USER` (tiền tố `kt-browser-eval-`), `KT_EVAL_BROWSER_PASSWORD` và `KT_EVAL_BROWSER_SEED` (đường dẫn seed map ngoài repo), rồi chạy `python apps/backend/manage.py shell -c "import runpy; runpy.run_path('evals/vietnamese-journeys/seed_browser.py')"`. Chỉ đặt `KT_EVAL_BROWSER_REUSE=1` nếu muốn chạy lại organizer trên bộ mẫu đã có. Seeder kiểm tra tài khoản, ID và nguyên văn của tất cả ghi chú trước khi gán lại.

## Cách đọc báo cáo

[Kết quả Chromium sau khi sửa tìm theo trí nhớ](results-browser-memory-windows.json) được đo trên Windows với Chrome 158, mã ứng dụng `a0c7dc588c98683877835aadd3669f4314813bae` và cùng 36 ghi chú tự soạn. Chromium mở đúng nguyên văn 36/36 bài từ Thư viện. Sau khi khởi động lại pilot, M14 vẫn giữ lựa chọn gỡ “thu âm”.

| Kết quả trong năm bài đầu | Trước khi sửa | Lượt tìm mặc định sau sửa | Sau khi bấm “Tìm gần đúng” nếu cần |
| --- | --- | --- | --- |
| Mọi câu có bài đích | 16/36 | 22/36 | 36/36 |
| Diễn đạt theo trí nhớ | 3/21 | 8/21 | 21/21 |
| Dùng từ trong bài | 9/10 | 10/10 | 10/10 |
| Không dấu | 4/5 | 4/5 | 5/5 |
| Câu ở tập giữ lại có bài đích | 7/16 | 10/16 | 16/16 |
| Câu không có bài phù hợp nhưng có kết quả | 0/3 | 0/3 | 1/3 |

Ở lượt đầu, 22 bài tìm thấy đều ở vị trí đầu và mở đúng. Chromium bấm “Tìm gần đúng” cho 14 câu chưa tìm thấy bài và một câu có đáp án rỗng. Qua cả hai lượt, cả 36 lần mở từ kết quả đều đúng địa chỉ, tiêu đề và Markdown gốc. Bấm mở rộng có thể đưa thêm gợi ý sai. Đáp án của bộ này là đáp án tạm do người soạn đặt.

Bộ hồi quy P16 độc lập với bộ 36 bài trên dùng 28 mục, 86 truy vấn và PostgreSQL QA. Lượt mặc định giữ Recall@5 73/77 và Precision@5 73/76. Cả 13 truy vấn âm đều trả rỗng và phép kiểm quyền, nguồn chứng cứ đều đạt. [Báo cáo P16 tại cùng bản mã](results-p16-memory-windows.json)

[Báo cáo Chromium trên Windows](results-browser-windows.json) ghi 36 truy vấn tìm ghi chú đích và ba truy vấn được kỳ vọng trả rỗng. Với mỗi mục đích trong năm kết quả đầu, Chromium bấm đúng kết quả và đối chiếu tiêu đề, địa chỉ và Markdown gốc. Báo cáo cũng ghi việc mở từng mục từ danh sách Thư viện, số chủ đề và số gán tự động của pilot. Số liệu thời gian tính từ lần bấm tìm hoặc mở kết quả đến khi giao diện hiển thị. Đáp án là nhãn tạm của người soạn bộ thử.

Trên bản `376d51d5bf78404b5f22c042c555b059225bd92a`, Chromium mở đúng cả 36 ghi chú từ Thư viện. Tìm kiếm đưa mục đích lên đầu với 16/36 truy vấn, trong đó có 7/16 truy vấn của tập giữ lại. Cả 16 lượt mở từ kết quả đều đúng và cả ba truy vấn âm đều trả rỗng. Pilot có 21 gán tự động trên 19 ghi chú.

Ở lượt thử thao tác sửa, menu Explorer đã gỡ `thu âm` khỏi M14. Sau khi chạy lại organizer, Chromium vẫn đọc được M14 với nhãn đã gỡ. Lần đo trên bản ứng viên ghi `VERIFIED_ABSENT`, và truy vấn PostgreSQL xác nhận dấu gỡ vẫn được lưu.
