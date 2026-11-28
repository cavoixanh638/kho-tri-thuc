# Đo khả năng xếp nhóm và tìm lại ghi chú tiếng Việt

Vietnamese Embedding v2 và bộ xếp hạng lại BGE đã được chạy thử bằng CPU trên bộ 120 ca. [So sánh ba cấu hình trên Windows](semantic-pilot/README.md)

**Bộ 120 tình huống mới** đo tìm theo trí nhớ, mã và đơn vị dễ nhầm, bộ lọc, thùng rác và phân biệt hai chủ kho trên 122 ghi chú tự soạn. Mỗi câu có đáp án, căn cứ và thứ tự kết quả ở cả lượt đầu lẫn khi dùng thêm **Tìm gần đúng**. [Xem 120 ca và kết quả](scenario-matrix/README.md)

Đợt 26/11/2026 kiểm thêm các cặp ghi chú dễ nhầm, cách giữ nguyên mã và số trong câu, cùng thao tác đổi bộ lọc và quay lại trên trình duyệt. [Bộ 21 câu mới](confusable-cases/README.md) · [Kết quả điều hướng Chromium](results-browser-navigation-20261126.json) · [Kiểm thử hai bộ tiếng Việt cũ và P16](edge-regression-20261126.json)

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

<a id="tim-theo-tri-nho"></a>

### Tìm theo trí nhớ trong ứng dụng

Trước đây, `plainto_tsquery` nối các từ bằng điều kiện AND. Tìm chuỗi con cần nguyên cụm, còn sửa lỗi gõ chỉ chạy cho truy vấn một từ. Vì vậy một từ khác cách tác giả viết đã đủ làm cả câu trả rỗng. Ví dụ, “mất đuôi câu nói” có thể chỉ khớp “mất” và “câu” trong bài **Âm cuối lời bị cụt**.

Bản Windows `a0c7dc5` tìm chính xác trước. Khi lượt này rỗng, ứng dụng bỏ các từ dẫn câu hỏi và tra chỉ mục của các ghi chú còn hiển thị cho đúng người, chủ đề, dự án và thẻ. Khớp tiêu đề, từ ít gặp và cặp từ đứng gần nhau được ưu tiên. Mã định danh và số trong câu phải có trong bài. Bằng chứng mạnh có thể xuất hiện ngay, những bài chỉ khớp một phần nhỏ cần người dùng chọn **Tìm gần đúng**. Mỗi kết quả có đoạn văn để đối chiếu.

| Câu hỏi và tiêu chí | Trước sửa | Lượt tìm đầu | Tính cả khi chọn **Tìm gần đúng** |
| --- | ---: | ---: | ---: |
| Tìm đúng bài trong top 5, bộ gốc | 16/36 | 22/36 | 36/36 |
| Trong đó, câu nhớ ý | 3/21 | 8/21 | 21/21 |
| Câu không có bài đúng nhưng nhận kết quả, bộ gốc | 0/3 | 0/3 | 1/3 |
| Tìm đúng bài trong top 5, bộ 36 câu nhớ ý mới | 0/36 | 1/36 | 34/36 |
| Câu không có bài đúng nhưng nhận kết quả, bộ mới | 0/15 | 0/15 | 10/15 |

Ở cột cuối, phép đo chỉ mở rộng khi giao diện cho phép và bài đích còn thiếu trong năm kết quả đầu. Đó là khả năng tìm lại khi sử dụng nút gợi ý. Người thật có nhận ra nút, chọn đúng phương án và mất bao lâu vẫn cần đo riêng. [Bộ gốc trước sửa](results-windows-after.json) · [Bộ gốc sau sửa](recall-original-after.json) · [Câu mới trước sửa](recall-frozen-before.json) · [Câu mới sau sửa](recall-frozen-after.json) · [Nghiệm thu trong Chromium](README-browser.md)

Một tác nhân khác đã soạn 36 câu nhớ ý và 15 câu âm từ nội dung ghi chú rồi khóa tệp trước khi xem thuật toán hoặc xếp hạng. Kết quả tổng hợp của lần thử đầu cho thấy trả gợi ý yếu tự động gây nhầm, vì vậy lần nghiệm thu cuối phân biệt lượt mặc định và lượt mở rộng. Hai bài còn trượt trên bộ mới là M03 và M06. [Tệp câu hỏi đã khóa](recall-check.json)

Chạy lại trong môi trường QA như phần trên. Tệp JSON giữ danh sách kết quả theo từng câu, kết quả lượt đầu, việc có mở rộng và nguồn gốc đáp án.

```powershell
python evals/vietnamese-journeys/evaluate.py --run original.json --follow-suggestions
python evals/vietnamese-journeys/evaluate.py --gold evals/vietnamese-journeys/recall-check.json --run recall.json --follow-suggestions
```

### Phép thử ngoại tuyến trước khi sửa

Lệnh `python evals/vietnamese-journeys/compare_partial_match.py` giữ nguyên mọi kết quả tìm kiếm đã có. Với truy vấn trả rỗng, phép thử xét các bài có ít nhất hai từ chung với câu hỏi sau khi bỏ dấu, ưu tiên từ hiếm trong bộ 36 bài. Số bài đích vào top 5 tăng từ 16/36 lên 36/36, trong đó nhóm nhớ ý tăng từ 3/21 lên 21/21. Cả 3 câu hỏi đáng lẽ trả rỗng cũng nhận gợi ý sai. Trong 16 bài giữ lại, số tìm trúng tăng từ 7 lên 16 và cả 2 câu âm đều có kết quả.

Phép so sánh này dùng tiêu đề và nội dung ghi chú tự soạn. Bảng trên ghi kết quả thực tế sau khi tính năng được đưa vào ứng dụng.
