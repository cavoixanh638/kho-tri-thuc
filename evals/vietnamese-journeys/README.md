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

Sau khi chấm xong, runner thử bổ sung một chủ đề bị thiếu qua API, chạy lại job và đọc lại. Runner cũng gửi danh sách chủ đề mong muốn cho một mục có nhãn tự động sai, kiểm lại ngay sau PATCH và sau job. Mỗi thao tác có kết quả riêng. Nếu một thao tác sửa thất bại, runner vẫn xuất báo cáo rồi trả exit code 1. Đây là phép thử hành trình dùng thực tế trên API, kể cả khi endpoint PATCH hiện chỉ được thiết kế quản lý các gán do người dùng tạo.

Kết quả Windows đã ghi trong `results-windows.json`, kèm mã nguồn, hash corpus/nhãn/evaluator và từng ca. Không suy số liệu của bộ tổng hợp thành chất lượng trên ghi chú cá nhân.
