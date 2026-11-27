# Thử mở rộng ứng viên khi bấm Tìm gần đúng

## Kết quả phép thử chính

Ngày 27/11/2026, bản `f6c7a21` được đối chiếu với backend `f62b32c` qua API có đăng nhập, trên Windows với PostgreSQL và BGE chạy thật trên CPU. Cả 520 phản hồi mặc định trùng nguyên JSON, gồm thứ tự, đoạn trích, điểm, con trỏ và trạng thái nút. Phương án thử tắt sẵn.

| Chỉ số | Bản hiện tại | Mở rộng danh sách ngắn |
| --- | ---: | ---: |
| 120 câu cũ, mặc định | 87/120 | 87/120 |
| 120 câu cũ, có dùng nút khi được đề nghị | 117/120 | 118/120 |
| 400 câu mới, mặc định | 146/400 | 146/400 |
| 400 câu mới, có dùng nút khi được đề nghị | 235/400 | 236/400 |
| Câu nhớ ý một đáp án, ghi chú đúng đứng đầu | 179/224 | 179/224 |
| Câu nhiều đáp án, đủ ghi chú trong top 5 | 15/27 | 16/27 |
| Câu không có đáp án nhưng vẫn có kết quả ở lượt cuối (bấm nếu có nút) | 108/125 | 108/125 |
| Tổng số mục trả về sai trên các câu không đáp án | 461 | 461 |
| P95 một lượt bấm trên bộ mới, 323 lượt | 638 ms | 1.113 ms |

Cải thiện ở bộ cũ là L13, hỏi về buổi chỉ ráp bè cuối bài. Chromium xác nhận ghi chú đúng từ vắng mặt lên hạng 1 khi bấm nút, hai ghi chú cũ vẫn theo đúng thứ tự, quay lại khôi phục màn hình ban đầu. Bộ mới chỉ có C29d tăng điểm nhờ tìm đủ hai ghi chú sửa màn sân khấu. Chênh lệch là **+0,25 điểm phần trăm**, khoảng bootstrap theo cụm 95% từ **0 đến +0,75 điểm**. Chưa đạt điều kiện bật rộng đã chốt. [120 kết quả theo cặp](results-120-windows.json) · [400 kết quả theo cặp](results-400-windows.json) · [Kiểm chứng Chromium](browser-l13-windows.json)

Trên bộ mới, 323 câu hiện nút, 256 lượt đã có đủ năm kết quả và 67 lượt có chỗ trống. Sau các kiểm tra ràng buộc và tìm ứng viên, BGE chấm thêm 194 cặp ở 33 lượt và chỉ nhận một mục. Trong 125 câu không có đáp án, 4 câu nhận kết quả ngay ở lượt đầu. Có 105 câu có kết quả sai sau khi thực sự bấm nút. Ba câu khác chỉ có kết quả mặc định và cũng sai, nâng tổng số câu có kết quả sai ở lượt cuối lên 108. Cả hai cấu hình có cùng kết quả ở nhóm này. Không có kết quả vượt phạm vi trên hai bộ.

Hai cấu hình đo thời gian ở hai lượt chạy nối tiếp sau khi nạp mô hình. Số P95 mô tả độ trễ API trên máy thử. Kiểm tra hồi quy backend có 469 kiểm thử đạt và 9 bỏ qua. Bộ P16 gồm 86 truy vấn xác nhận Recall@5 đạt 73/77, Precision@5 đạt 73/76 và cả 13 câu cần trả rỗng đều trả rỗng. [Các kiểm thử riêng cho nhánh mở rộng](../../../apps/backend/search/test_memory_candidates.py) · [Bộ P16](../../../tools/search/p16_eval.py)

## Thăm dò thêm trên trang đã đầy

Sau khi xem độ phủ của phép thử chính, nhóm đo thêm một phương án ngoại tuyến, cho cả các trang đã có năm mục. Đầu vào là danh sách thực tế của bản đối chứng sau khi bấm nút. Chỉ xét truy vấn văn xuôi có ít nhất bốn từ mang thông tin, giữ nguyên bộ lọc và bỏ qua câu có ràng buộc cụ thể. Mô hình Vietnamese Embedding v2 lấy tối đa 12 ứng viên gần nhất trong phạm vi, hợp thứ hạng với tối đa năm gợi ý đã có bằng RRF (hằng số 60), rồi BGE chấm tối đa tám ứng viên đầu. Chỉ giữ mục có logit từ −2. Quy tắc, phiên bản mô hình và ngưỡng lấy từ phép thử cũ. Một đối chứng phụ dùng BGE lọc và xếp hạng lại các ứng viên cũ với cùng ngưỡng. Cách này tách tác dụng của bộ lọc và xếp hạng khỏi tác dụng của việc thêm ứng viên bằng embedding. [Mã phép thăm dò](shadow.py) · [Cấu hình đã hiệu chỉnh](../semantic-pilot/calibration-windows.json)

| Kết quả sau khi bấm nếu có nút | Hiện tại | BGE lọc và xếp lại ứng viên cũ | Thêm embedding và lọc bằng BGE |
| --- | ---: | ---: | ---: |
| Tổng đạt, 120 câu cũ | 117/120 | 116/120 | 117/120 |
| Tổng đạt, 400 câu mới | 235/400 | 226/400 | 230/400 |
| Nhớ ý một đáp án, đúng hạng 1 | 179/224 | 162/224 | 165/224 |
| Nhiều đáp án, đủ trong top 5 | 15/27 | 9/27 | 10/27 |
| Câu không có đáp án vẫn có kết quả ở lượt cuối | 108/125 | 94/125 | 94/125 |
| Tổng số mục sai trong các câu không có đáp án | 461 | 135 | 135 |

Phương án rộng thử trên 304 lượt bấm của bộ mới, gồm đủ 256 trang đã đầy. So với hệ thống hiện tại, 18 câu chuyển từ sai sang đúng và 23 câu từ đúng sang sai. So với chỉ lọc BGE, embedding cứu thêm bốn câu, gồm ba câu nhớ ý. Việc giảm số câu âm nhận gợi ý đến từ ngưỡng lọc BGE. Cũng chính ngưỡng này khiến nhiều câu có đáp án bị trả rỗng. Trên bộ cũ, phương án rộng cứu L13 nhưng làm trượt L25. Bản đang dùng tiếp tục phù hợp hơn cho câu chỉ nhớ ý trên tập thử này. [Kết quả ngoại tuyến từng câu](semantic-shadow-windows.json)

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

Phép thăm dò đọc hai báo cáo theo cặp và các trọng số đã chuẩn bị theo hướng dẫn semantic-pilot. Chạy `python evals/vietnamese-journeys/memory-400/shadow.py --models THU_MUC_MODELS --output shadow-local.json` từ thư mục gốc. Tốc độ P95 trong bảng chính chỉ tính hai cấu hình chạy qua API. [Chuẩn bị mô hình](../semantic-pilot/README.md)
