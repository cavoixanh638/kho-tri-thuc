# Thử mở rộng ứng viên khi bấm Tìm gần đúng

## Thiết kế chốt trước khi chấm

Đối chứng là bản `f62b32c` dùng PostgreSQL mặc định và BGE khi mở gợi ý. Chỉ thử tìm thêm ứng viên sau khi người dùng bấm nút vốn có, ở trang đầu có từ một đến bốn gợi ý và còn chỗ hiển thị. Giới hạn thí nghiệm ở truy vấn văn xuôi có ít nhất bốn từ mang thông tin. Câu có mã, số, trích dẫn hoặc ràng buộc cụ thể đã được nhận diện dùng đường tìm hiện hành.

PostgreSQL lấy thêm tối đa tám ghi chú cùng phạm vi có manh mối từ vựng, cho phép ít từ trùng hơn lượt tìm ban đầu. Mỗi ứng viên phải thỏa điều kiện bằng chứng của nguồn. BGE cục bộ chấm các ghi chú cũ và mới. Chỉ thêm tối đa một mục nếu điểm thô đạt ngưỡng −2 của phép hiệu chỉnh cũ và cao hơn mục cũ tốt nhất ít nhất một đơn vị logit. Nếu thiếu mô hình hoặc bằng chứng thì dùng danh sách cũ. [Phép hiệu chỉnh độc lập trước đó](../semantic-pilot/calibration-windows.json)

Ba bộ mới có 100 cụm tình huống, mỗi cụm bốn câu có ý định khác nhau và các ghi chú cùng chủ đề dễ nhầm. Ba người soạn bằng AI làm việc độc lập với mã tìm kiếm và kết quả mô hình. Dùng toàn bộ 120 câu cũ để phát triển và kiểm tra hồi quy. Giữ kín toàn bộ 400 câu mới cho một lần đối chiếu cuối với quy tắc cố định. Cả hai cấu hình tìm trên cùng kho gộp của 400 câu. Chạy riêng 120 câu trên kho cũ để giữ nguyên kết quả đối chứng.

Mỗi câu một đáp án cần đứng đầu, câu nhiều đáp án cần đủ trong top 5, câu không có đáp án phải trả rỗng. Hai cấu hình phải trả giống hệt lượt đầu, gồm thứ tự và trạng thái nút. Đo thêm số câu thật sự thấy nút, số câu đủ điều kiện thử, số ứng viên mới hiển thị, số lần đúng thành sai hoặc sai thành đúng, số mục gợi ý sai ở câu âm và số kết quả vượt bộ lọc. Câu âm vốn đã có gợi ý vẫn có thể nhận thêm một mục sai. Đếm riêng trường hợp này.

Tiêu chí chính là chênh lệch tỷ lệ đạt trên toàn bộ 400 câu theo cặp. Ước lượng khoảng 95% bằng cách lấy mẫu lại 100 cụm, giữ bốn câu của mỗi cụm cùng nhau. Báo riêng nhóm nhớ ý và các câu thật sự mở được gợi ý. Chỉ đề xuất bật rộng nếu cận dưới của khoảng chênh lệch lớn hơn 0, lượt mặc định giữ nguyên, không có kết quả ngoài phạm vi và số mục gợi ý sai trên các câu âm không tăng ở cả hai bộ. Nếu chưa đủ bằng chứng thì giữ chế độ thử tắt sẵn. Khoảng ước lượng mô tả biến động giữa các cụm tự soạn. Độ chính xác trên thư viện sử dụng thực tế cần dữ liệu người dùng được phép đánh giá.

## Tập câu hỏi và chấm chéo

400 câu dùng chung 304 ghi chú. Có 224 câu nhớ ý một đáp án, 125 câu không có đáp án, 27 câu cần tìm đủ nhiều ghi chú và 24 câu đối chứng một đáp án. Chủ kho, thùng rác, chủ đề, dự án, thẻ và mục bị loại đều có ca kiểm tra. Các tập đáp án được đối chiếu với phạm vi trước khi đo. [Sinh hoạt](home.json) · [Thủ công và nghệ thuật](craft.json) · [Hoạt động cộng đồng](community.json)

Chọn ngẫu nhiên tám cụm từ mỗi người soạn để chấm chéo 96 câu trước khi xem kết quả tìm kiếm. Người chấm chỉ nhận câu hỏi, ghi chú của chủ đề và bộ lọc. Lần đầu hai bên trùng nguyên tập đáp án ở 89/96 câu. Bảy bất đồng thuộc nhóm thủ công, chủ yếu do ghi chú có nhắc đúng chủ đề nhưng mô tả thao tác đối nghịch với điều được hỏi. Sau khi làm rõ một câu có thể hiểu là hỏi có/không và bổ sung đúng chủ kho vào bộ lọc, một người chấm độc lập khác nhận 32 câu thủ công với mã câu ẩn danh, theo thứ tự ngẫu nhiên. Kết quả trùng đáp án ở 32/32 câu. Bốn câu ở hai nhóm còn lại cũng được sửa chi tiết phụ theo góp ý trước khi khóa đề. Các tác giả và người chấm đều là AI, mới chấm chéo một phần kho câu hỏi. [Phiếu chấm và bất đồng ban đầu](blind-label-review.json)

## Cần bao nhiêu câu

Nếu lấy mẫu ngẫu nhiên **độc lập** để ước lượng một tỷ lệ, với 95% tin cậy và giả định bảo thủ tỷ lệ gần 50%, khoảng 385 câu cho sai số xấp xỉ ±5 điểm phần trăm, 1.068 câu cho ±3 điểm. 400 câu trong phép thử này thuộc 100 tình huống và cùng dùng dữ liệu tự soạn. Bốn câu về cùng tình huống có thể cùng khó hoặc cùng dễ. Vì vậy phân tích chênh lệch giữa hai bản lấy mẫu lại nguyên cụm 10.000 lần, với hạt giống cố định, và báo số lượt bấm thực tế chịu tác động. [Công thức chọn cỡ mẫu của NIST](https://itl.nist.gov/div898/handbook/ppc/section3/ppc333.htm) · [Phương pháp bootstrap cho dữ liệu theo cụm](https://link.springer.com/article/10.3758/s13428-019-01252-y)

## Chạy lại

Hai bản cần cùng bộ trọng số BGE. Từ thư mục gốc của bản có bộ chấm, dùng Python của backend, đặt `KT_EVAL_ALLOW_DISPOSABLE=1` và chọn cơ sở PostgreSQL đã migrate, đang trống, tên `kt_eval_edge_pairs` trên loopback. Thay `../baseline` bằng checkout có backend `f62b32c`. Hai lệnh tìm chạy nối tiếp, mỗi lệnh tự hoàn tác ghi chú và tài khoản giả lập. Tệp đầu ra cần là tên mới.

```powershell
python evals/vietnamese-journeys/memory-400/run.py --suite 400 --validate
python evals/vietnamese-journeys/memory-400/run.py --suite 400 --mode control --backend ../baseline --expected-source f62b32c --output control-400.json
python evals/vietnamese-journeys/memory-400/run.py --suite 400 --mode trial --backend . --expected-source f6c7a21 --output trial-400.json
python evals/vietnamese-journeys/memory-400/compare.py --control control-400.json --trial trial-400.json --output compared-400.json
```

Dùng `--suite 120` và các tên tệp khác khi chạy hồi quy. Bộ chấm đối chiếu mã băm toàn bộ JSON trả về ở lượt đầu, thứ tự các mục cũ khi mở rộng và phạm vi của từng ID. Với cùng backend, `SEARCH_MEMORY_CANDIDATES=1` bật phép thử trong tiến trình ứng dụng. Cấu hình mặc định là `0`.
