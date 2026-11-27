# Thử mở rộng ứng viên khi bấm Tìm gần đúng

## Thiết kế chốt trước khi chấm

Đối chứng là bản `f62b32c` dùng PostgreSQL mặc định và BGE khi mở gợi ý. Chỉ thử tìm thêm ứng viên sau khi người dùng bấm nút vốn có, ở trang đầu có từ một đến bốn gợi ý và còn chỗ hiển thị. Giới hạn thí nghiệm ở truy vấn văn xuôi có ít nhất bốn từ mang thông tin. Câu có mã, số, trích dẫn hoặc ràng buộc cụ thể đã được nhận diện dùng đường tìm hiện hành.

PostgreSQL lấy thêm tối đa tám ghi chú cùng phạm vi có manh mối từ vựng, cho phép ít từ trùng hơn lượt tìm ban đầu. Mỗi ứng viên phải thỏa điều kiện bằng chứng của nguồn. BGE cục bộ chấm các ghi chú cũ và mới. Chỉ thêm tối đa một mục nếu điểm thô đạt ngưỡng −2 của phép hiệu chỉnh cũ và cao hơn mục cũ tốt nhất ít nhất một đơn vị logit. Nếu thiếu mô hình hoặc bằng chứng thì dùng danh sách cũ. [Phép hiệu chỉnh độc lập trước đó](../semantic-pilot/calibration-windows.json)

Ba bộ mới có 100 cụm tình huống, mỗi cụm bốn câu có ý định khác nhau và các ghi chú cùng chủ đề dễ nhầm. Ba người soạn bằng AI làm việc độc lập với mã tìm kiếm và kết quả mô hình. Dùng toàn bộ 120 câu cũ để phát triển và kiểm tra hồi quy. Giữ kín toàn bộ 400 câu mới cho một lần đối chiếu cuối với quy tắc cố định. Cả hai cấu hình tìm trên cùng kho gộp của 400 câu. Chạy riêng 120 câu trên kho cũ để giữ nguyên kết quả đối chứng.

Mỗi câu một đáp án cần đứng đầu, câu nhiều đáp án cần đủ trong top 5, câu không có đáp án phải trả rỗng. Hai cấu hình phải trả giống hệt lượt đầu, gồm thứ tự và trạng thái nút. Đo thêm số câu thật sự thấy nút, số câu đủ điều kiện thử, số ứng viên mới hiển thị, số lần đúng thành sai hoặc sai thành đúng, số mục gợi ý sai ở câu âm và số kết quả vượt bộ lọc. Câu âm vốn đã có gợi ý vẫn có thể nhận thêm một mục sai. Đếm riêng trường hợp này.

Tiêu chí chính là chênh lệch tỷ lệ đạt trên toàn bộ 400 câu theo cặp. Ước lượng khoảng 95% bằng cách lấy mẫu lại 100 cụm, giữ bốn câu của mỗi cụm cùng nhau. Báo riêng nhóm nhớ ý và các câu thật sự mở được gợi ý. Chỉ đề xuất bật rộng nếu cận dưới của khoảng chênh lệch lớn hơn 0, lượt mặc định giữ nguyên, không có kết quả ngoài phạm vi và số mục gợi ý sai trên các câu âm không tăng ở cả hai bộ. Nếu chưa đủ bằng chứng thì giữ chế độ thử tắt sẵn. Khoảng ước lượng mô tả biến động giữa các cụm tự soạn. Độ chính xác trên thư viện sử dụng thực tế cần dữ liệu người dùng được phép đánh giá.
