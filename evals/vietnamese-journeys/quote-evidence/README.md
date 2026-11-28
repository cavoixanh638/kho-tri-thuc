# Trích bằng chứng khi bấm Tìm gần đúng

Trên bộ 400 câu, bộ đọc cục bộ tăng số câu tìm đúng từ **235 lên 256**. Trong 33 câu của cả ba bộ mà ghi chú đủ căn cứ trả lời **Không**, ứng dụng trả đúng nhãn và đúng ghi chú 13 lần. Chỉ **2/33** lần phần nguyên văn hiển thị đủ để người đọc xác minh câu trả lời. Thử nghiệm tắt sẵn.

## Điểm tìm kiếm qua API của app

Mỗi bộ dùng một kho ghi chú tự soạn riêng và tài khoản QA có đăng nhập. Mỗi câu được tìm theo cách mặc định, sau đó bấm **Tìm gần đúng** đúng một lần nếu ứng dụng có nút. Có một đáp án thì ghi chú đúng phải đứng đầu, có nhiều đáp án thì cần tìm đủ trong năm mục đầu, còn nhãn rỗng yêu cầu trang rỗng. Các câu và đáp án đã khóa từ trước. Điểm ở bảng này đo khả năng tìm ghi chú.

| Bộ | Chỉ lượt mặc định | Bấm nút cũ khi có | Bấm nút có trích dẫn khi có | Số lượt bấm | Lượt qua bộ đọc |
| --- | ---: | ---: | ---: | ---: | ---: |
| 120 câu hồi quy | 87/120 | 117/120 (97,50%) | 117/120 (97,50%) | 34 | 1 |
| 400 câu chính | 146/400 | 235/400 (58,75%) | 256/400 (64,00%) | 323 | 72 |
| 48 câu giữ lại | 22/48 | 33/48 (68,75%) | 33/48 (68,75%) | 37 | 7 |
| 36 câu đối chiếu bổ sung | 21/36 | 18/36 (50,00%) | 21/36 (58,33%) | 25 | 21 |

Ở bộ 400, **23 câu chuyển từ trượt sang đạt** do các gợi ý biến mất ở câu có nhãn rỗng. Hai câu H03b và C06b mất ghi chú đúng. Do đó nhóm có đáp án giảm **218 xuống 216/275**, nhóm cần trả rỗng tăng **17 lên 40/125**. Mức tăng chung 5,25 điểm phần trăm có khoảng bootstrap 95% từ **3,00 đến 7,75 điểm** khi lấy mẫu lại 100 cụm tình huống. Khoảng này chỉ mô tả bộ tự soạn.

Để kiểm xem mức tăng đến từ đâu, có thể lấy đúng các trang được đưa qua bộ đọc và luôn cho chúng trả rỗng. Đối chứng này đạt **116/120, 294/400 và 40/48**. Nhiều câu được đưa qua bộ đọc đồng thời có nhãn tìm kiếm rỗng. Điểm tổng vì thế có thể tăng ngay cả khi chưa xác minh được nội dung. Thử nghiệm Sol với ứng viên bổ sung từ QLVB trước đây đạt 115/120, 305/400 và 40/48 trong một quy trình khác. Phép thử trong app giữ nguyên nút và nguồn ứng viên hiện hành.

## Câu trả lời Không và trường hợp thiếu dữ kiện

Đợt rà riêng đánh dấu 33 câu mà ghi chú bác bỏ mệnh đề được hỏi. Trong đó 30 câu có nhãn tìm kiếm cũ là rỗng vì kho không có ghi chú xác nhận mệnh đề. Giữ nguyên nhãn tìm kiếm cho phép đối chiếu với những lần đo trước. Việc đúng hay sai khi app trả lời **Không** được chấm riêng theo chi tiết được hỏi, phạm vi, ghi chú và phần trích người dùng nhìn thấy. [Nhãn trước khi chạy](polarity-audit.json) · [Đọc từng trích dẫn sau khi chạy](semantic-review.json)

| Bộ | Có căn cứ trả lời Không | Đã qua bộ đọc | Đứng đầu đúng Không và đúng ghi chú | Trích dẫn đầu đủ chứng minh |
| --- | ---: | ---: | ---: | ---: |
| 120 | 2 | 1 | 1 | 1 |
| 400 | 18 | 16 | 7 | 1 |
| 48 | 13 | 7 | 5 | 0 |
| 36 bổ sung | 12 | 8 | 8 | 3 |

Ở ba bộ chính, 7/33 câu thiếu nút, 2 có nút nhưng bỏ qua bộ đọc, 4 đã đọc rồi trả rỗng, 7 trả **Có**, còn 13 trả **Không** đúng ghi chú. Hai trường hợp có trích dẫn đủ là L14 (chụp sơ đồ gian hàng) và T13a (quy định ở lớp đầu bể nông). Câu B02Q1 tìm đúng ghi chú, trả **Không** nhưng chỉ trích tiêu đề “Trà gừng”. Câu khẳng định Mai dùng ba lát gừng tươi và không dùng bột nằm ngay trong thân ghi chú. H17c chọn được đoạn nói giặt thêm hai lượt vẫn không thấy vết rồi gắn nhãn **Có** cho câu hỏi vết cam có tiếp tục lan hay không.

Bộ 36 gồm 12 tình huống, mỗi tình huống có một câu **Có**, một câu **Không** và một câu **thiếu dữ kiện**. Trong 8 câu thiếu dữ kiện thực sự qua bộ đọc, hệ thống để trống 3, đoán **Không** ở 4 và đoán **Có** ở 1. Qua cả 604 truy vấn, hệ thống từng hiển thị **Không** ở 43 câu. Người rà chỉ tìm được đủ bằng chứng trong phần trích đầu ở **5/43** câu. Các nhãn và phần rà ngữ nghĩa do AI lập trên dữ liệu mô phỏng. [Bộ đối chiếu 36 câu](contrast-36.json)

## Cách hoạt động và phạm vi phép đo

Lượt mặc định dùng PostgreSQL. Khi bấm nút, ứng dụng giữ cách lấy ứng viên và xếp hạng BGE sẵn có. Với câu hỏi đóng hoặc yêu cầu tìm ghi chú xác nhận một chi tiết, bộ đọc nhận câu hỏi gốc và tối đa năm ghi chú trong phạm vi được phép xem. Mỗi ghi chú có thể cung cấp tối đa năm đoạn nguyên văn, mỗi đoạn tối đa 270 ký tự. Mô hình chọn ghi chú, nhãn và chỉ số đoạn. API tự lấy lại chữ từ đúng đoạn trong ghi chú. Quyền chủ sở hữu, mục đã xóa và các bộ lọc tiếp tục áp dụng trước bước này.

Mỗi trang được kiểm tra tối đa năm ứng viên, kể cả khi giao diện yêu cầu 25 mục. Người dùng có thể chuyển tiếp nếu còn ứng viên. Nếu reader không trả lời hợp lệ trong thời gian chờ, app trả lại toàn bộ trang gợi ý cũ và thông báo trạng thái. Thử nghiệm dùng BGE ONNX và Qwen3-4B-Instruct-2507 Q4_K_M qua llama.cpp b12753 trên Intel Core i5-12400 và iGPU UHD 730. Không gọi nhà cung cấp tính tiền theo token. [Cấu hình và cách bật thử](LOCAL_SETUP.md) · [Chạy lại với tài khoản QA](REPLAY.md)

## Thời gian chờ và chi phí mỗi lần bấm

Đã đo tuần tự trên ba bộ chính. 568 phản hồi mặc định và điều kiện hiện nút trùng nội dung giữa bản gốc, bản thử tắt cờ và bản bật cờ. 394 câu có nút. Ở 314 lượt bộ đọc được bỏ qua, trang gợi ý trùng bản gốc. Cả 80 lượt cần đọc đều trả về hợp lệ. Trên cả 36 câu bổ sung, kết quả mặc định cũng trùng. Tính chung bốn bộ, có 101 lượt đọc thật và không có trích dẫn lấy từ bên ngoài ghi chú hiển thị. [Kết quả từng câu](cases.jsonl)

| Nhóm lượt bấm thực trong 3 bộ | Số lượt | Tắt trích dẫn, P50 / P95 | Bật trích dẫn, P50 / P95 | Điện gói xử lý trung bình, tắt → bật |
| --- | ---: | ---: | ---: | ---: |
| Tất cả lượt bấm | 394 | 0,486 / 0,601 giây | 0,552 / 9,368 giây | 0,00427 → 0,01875 Wh |
| Thực sự cần đọc | 80 | 0,484 / 0,582 giây | 8,084 / 9,800 giây | 0,00427 → 0,06997 Wh |
| Bỏ qua bộ đọc | 314 | 0,490 / 0,607 giây | 0,519 / 0,683 giây | 0,00426 → 0,00570 Wh |

Số giây tính từ lúc gửi GET qua Django test client đã đăng nhập đến khi nhận toàn bộ phản hồi. BGE đã được làm nóng. Reader chạy sẵn, nạp mô hình tới lúc sẵn sàng mất 10,60 giây trong lần đo riêng. P50 dùng trung vị, P95 lấy quan sát ở bậc phần trăm 95 làm tròn lên. Các ca có xác minh dùng tổng cộng **45.292 token đầu vào và 1.068 token đầu ra**. Phí API bên ngoài là **0 USD mỗi lượt**.

Điện năng là chênh lệch đồng hồ gói xử lý Intel trước và sau từng lượt, gồm CPU, iGPU và tải nền trong khoảng đó. Con số chưa bao gồm điện của phần còn lại của máy, điện giữ bộ đọc chờ và giá phần cứng. Với giá minh họa **3.000 đồng/kWh**, phần điện gói xử lý trong một lượt thực sự đọc vào khoảng **0,21 đồng**, tăng **0,20 đồng** so với cùng các câu khi tắt. Dùng giá điện thực tế bằng cách lấy Wh nhân đồng/kWh rồi chia 1.000. [Số đo thời gian, điện năng và token](pooled.json) · [Windows Energy Meter Interface](https://learn.microsoft.com/en-us/windows-hardware/drivers/powermeter/energy-meter-interface)

## Kiểm chứng qua giao diện Windows

Chrome 158 chạy giao diện đã build với API, PostgreSQL, BGE và Qwen thật. Từ thời điểm bấm nút đến khi DOM hiển thị, L14 (Không) mất **10,22 giây**, PC02a (Có) **4,80 giây**, PC04c (thiếu dữ kiện) **2,59 giây** và H03b (bỏ sót ghi chú đúng) **8,87 giây**. Mỗi câu đo một lần. Cả bốn yêu cầu lấy 25 mục và đều quay về đúng kết quả ban đầu. Hai câu có trích dẫn mở được đúng ghi chú gốc. H03b chuyển tiếp được sang trang đã kiểm thứ hai dù trang đầu rỗng. [Bằng chứng Chromium và mã băm](validation-windows.json)

93 kiểm thử Django của phần tìm kiếm và 338 kiểm thử frontend đã đạt. Trình tái lập công khai chạy thêm bộ 120 qua đăng nhập có CSRF, đạt 117/120 và khớp toàn bộ kết quả mặc định lẫn các ghi chú hiển thị sau khi bấm. Mã ứng dụng được so từ `37dd5c9` đến `4fc2578`. Để đối chiếu lần đo trên mã đang làm với mã đã commit, bản tắt cờ đã chạy lại cả 604 câu trên cùng bộ tệp Python backend. [Dữ liệu xác minh](validation-windows.json)

Trong 57 câu có đáp án mà bản cũ tìm trượt ở bộ 400, chỉ **4 câu** có đủ đáp án trong năm kết quả hiển thị để việc đổi thứ tự có thể sửa được. **53 câu** thiếu ít nhất một ghi chú cần thiết, gồm 33 câu không hiện nút và 20 câu đã bấm. Muốn cải thiện tỷ lệ tìm thấy tài liệu, hướng thử tiếp là tăng độ bao phủ ứng viên cho hai nhóm này rồi đo trên câu mới. Khi chẩn đoán riêng phần đọc, cả **24/24** câu có đáp án “Không” đã đi qua mô hình ở ba bộ chính đều có sẵn ghi chú bác bỏ trong danh sách đầu vào. Với nhóm này, nên chọn câu có chi tiết quyết định trong thân ghi chú trước, sau đó mới gắn nhãn **Có** hoặc **Không**. [Từng danh sách ứng viên và đáp án](cases.jsonl)
