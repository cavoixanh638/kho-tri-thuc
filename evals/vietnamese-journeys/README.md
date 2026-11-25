# Đo khả năng xếp nhóm và tìm lại ghi chú tiếng Việt

36 ghi chú được soạn riêng cho phép thử, gồm 20 mục phát triển và 16 mục giữ lại. Nội dung bao phủ ảnh, âm thanh, dựng phim, sao lưu, dẫn nguồn, golf và những mục nên để trống. Hai ghi chú thuộc nhiều chủ đề. Một số ghi chú nhắc tên chủ đề trong ngữ cảnh không liên quan. Mỗi mục có một truy vấn tìm lại chính mục đó. Ba truy vấn bổ sung không có mục phù hợp.

`corpus.json` chứa văn bản và danh sách chủ đề. `provisional.json` chứa đáp án do cùng người soạn bộ thử đặt trước lần đo. Các mục giữ lại vẫn dùng đáp án tạm này. Khi thay đổi thuật toán, chỉ dùng tập phát triển để chọn tham số và công bố riêng số liệu trên tập giữ lại. Dùng bộ mới cho một vòng đánh giá độc lập sau khi đã xem lỗi ở tập giữ lại.

## Chạy từ gốc repo

```powershell
python evals/vietnamese-journeys/evaluate.py --validate
python evals/vietnamese-journeys/evaluate.py --blank-review review-private.json
```

Lệnh thứ hai tạo phiếu mới độc lập với tệp đáp án. Người chấm đọc ghi chú, điền chủ đề muốn gán hoặc để `[]` nếu nên giữ ở phần chưa phân loại, viết cụm tìm kiếm của mình và chọn `query_kind` tương ứng (`literal`, `memory` hoặc `unaccented`). Đặt `reviewed` cho từng mục đã xét. Nếu chấm trước khi xem đáp án và kết quả máy thì đặt `attest_before_results` thành `true`. Có thể bổ sung truy vấn không có kết quả mong muốn bằng một bản ghi `{"split":"holdout","query":"..."}` trong `negative_queries`. Giữ phiếu riêng. Với kho tự chọn, truyền cùng tệp `--corpus` khi sinh phiếu và khi đo.

Chạy bằng Python của backend và một PostgreSQL cục bộ dành riêng cho QA. Đặt các biến kết nối Django theo `apps/backend/config/settings.py` với `POSTGRES_HOST=127.0.0.1`, tên DB bắt đầu bằng `kt_eval_`, `DJANGO_ALLOWED_HOSTS` có `localhost`. Tạo và migrate DB sạch trước. Runner kiểm tra tên DB đang kết nối và từ chối nếu đã có người dùng hoặc Item. Dữ liệu được rollback sau cùng.

```powershell
$env:KT_EVAL_ALLOW_DISPOSABLE = '1'
python apps/backend/manage.py migrate --noinput
python evals/vietnamese-journeys/evaluate.py --run report-qa.json
python evals/vietnamese-journeys/evaluate.py --gold review-private.json --run report-reviewed.json
```

## Diễn giải kết quả

Runner chạy `organize_item` và truy vấn các gán tự động thật trong PostgreSQL. Độ chính xác tính theo số **nhãn** đúng trên số nhãn máy đã gán. Độ phủ tính theo số **mục có ít nhất một gán tự động** trên số mục mà đáp án có chủ đề. Recall tính theo số nhãn mong muốn mà máy tìm được. Một mục có thể được phủ mà vẫn thiếu một nhãn hoặc bị gán sai. Tỷ lệ cần sửa tính theo số mục có bất kỳ khác biệt nào giữa hai tập nhãn. Báo cáo giữ tử và mẫu, tỷ lệ rỗng là `null`.

SearchService chạy với tất cả mục cùng một chủ sở hữu, trên toàn bộ kho ở cả hai split. Một truy vấn dương đạt khi Item đích xuất hiện trong năm kết quả đầu. Có thể có thêm các mục hữu ích khác, nên báo cáo chỉ chấm khả năng tìm lại mục đích. Thời gian đo cho lời gọi dịch vụ trong process. Thời gian đọc trên trình duyệt và mở đúng đoạn nguồn cần phép thử riêng.

Sau khi chấm, runner thử hai thao tác. Với M01, người dùng ghim một chủ đề còn thiếu. Với M14, người dùng chọn **Bỏ khỏi nhánh** để gỡ chủ đề “thu âm” khỏi ghi chú về tiền cọc thuê ghế. Runner đọc lại dữ liệu ngay sau thao tác và sau khi chạy lại bộ phân nhóm. Trên bản ứng viên, cả hai lựa chọn đều được giữ. Nếu một thao tác thất bại, runner xuất báo cáo và trả exit code 1. [Trước khi sửa](results-windows.json) · [Sau khi sửa](results-windows-after.json)

Qua giao diện Windows, có thể đọc cả 36 bài và lặp lại phép thử bằng tài khoản pilot. Bộ chuẩn tạm có 36 câu hỏi tìm một bài xác định và 3 câu không có bài phù hợp. Câu hỏi được soạn trước phép đo. Người dùng chưa tự đặt câu hỏi sau một khoảng thời gian sử dụng. [Mở pilot và đọc kết quả trình duyệt](README-browser.md)

### Thử tìm theo một phần cụm từ

Lệnh `python evals/vietnamese-journeys/compare_partial_match.py` giữ nguyên mọi kết quả tìm kiếm đã có. Với truy vấn trả rỗng, phép thử xét các bài có ít nhất hai từ chung với câu hỏi sau khi bỏ dấu, ưu tiên từ hiếm trong bộ 36 bài. Số bài đích vào top 5 tăng từ 16/36 lên 36/36, trong đó nhóm nhớ ý tăng từ 3/21 lên 21/21. Cả 3 câu hỏi đáng lẽ trả rỗng cũng nhận gợi ý sai. Trong 16 bài giữ lại, số tìm trúng tăng từ 7 lên 16 và cả 2 câu âm đều có kết quả.

Đây là phép so sánh ngoại tuyến trên tiêu đề và nội dung ghi chú tự soạn. Đợt thử tiếp theo nên cho người dùng chủ động chọn “Tìm gần đúng” sau một lần tìm rỗng, rồi đo số lần gợi ý giúp họ mở đúng bài trên một bộ câu hỏi mới. Kết quả hiện tại đủ để thử cách đó trước khi cân nhắc tìm kiếm vector. Bản pilot đang dùng cách tìm mặc định đã đo qua trình duyệt.
