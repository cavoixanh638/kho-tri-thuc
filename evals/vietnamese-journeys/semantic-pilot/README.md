# Thử tìm theo nghĩa trên Windows

Ngày 26/11/2026, nhóm chạy ba cách tìm trên cùng 120 câu và 122 ghi chú tiếng Việt tự soạn. Cấu hình có bộ xếp hạng lại đạt 99/120, so với 92/120 của dịch vụ hiện tại khi dùng thêm **Tìm gần đúng**. Tuy nhiên, 18/26 câu không có đáp án vẫn nhận gợi ý, cao hơn mức 14/26 của bản đối chứng. **Đề xuất tiếp tục dùng cách tìm hiện tại cho người dùng.** [Đáp án đã khóa và các ghi chú](../scenario-matrix/README.md) · [Thứ hạng thực tế của từng cấu hình](results-windows.json)

## Kết quả trên 120 câu

| Tiêu chí | Tìm hiện tại, có mở rộng | Thêm embedding | Thêm embedding và xếp hạng lại |
| --- | ---: | ---: | ---: |
| Tổng ca đạt | 92/120 | 93/120 | 99/120 |
| Nhớ ý, phân biệt nghĩa | 28/40 | 24/40 | 29/40 |
| Mã, số, đơn vị và định dạng | 25/40 | 31/40 | 32/40 |
| Chủ kho, bộ lọc, trạng thái | 39/40 | 38/40 | 38/40 |
| Câu một đáp án có bài đúng đứng đầu | 70/81 | 72/81 | 78/81 |
| Câu nhiều đáp án có đủ bài trong năm mục đầu | 10/13 | 13/13 | 13/13 |
| Câu không có đáp án nhưng lại có kết quả | 14/26 | 18/26 | 18/26 |
| Ca có kết quả ngoài phạm vi cho phép | 0 | 0 | 0 |

Mốc đã đề xuất là vượt 28/40 ở nhóm nhớ ý, giảm gợi ý sai xuống dưới 14/26, đồng thời giữ các ca mã và phạm vi đã đạt. Cấu hình xếp hạng lại vượt mốc nhớ ý đúng một ca. Nó chuyển **12 ca từ sai thành đúng và 5 ca từ đúng thành sai**. Cả 5 ca hồi quy đều có trong kết quả công bố. [Các thay đổi theo ID](results-windows.json) · [Bộ chấm](judge.py)

- L16 hỏi học hát ở đâu sau khi cúp điện. Ghi chú đúng lên từ hạng 4 lên hạng 1. V04 viết `0.48 s` tìm đúng ghi chú chứa `0,48 s`.
- V35 hỏi mã `41/2023-TĐG` lại nhận tài liệu mang mã `14/2023-TĐG`. V40 hỏi tệp `.mp3` lại nhận mục có bản `.wav`. S32 hỏi móc số 2, chỉ có ở ghi chú đã xóa, lại nhận ghi chú đang dùng về móc số 6. Kết quả S32 nằm trong đúng chủ kho nhưng sai nội dung.
- Hai ca hồi quy còn lại là L25, hỏi buổi diễn đủ phục trang khi tắt loa, và V39, hỏi một dải độ ẩm loại hai giá trị biên. L25 trả rỗng dù có ghi chú đúng. V39 trả ghi chú mô tả dải tính cả hai giá trị biên.

### Nếu giữ đúng chỗ đang xuất hiện nút Tìm gần đúng

Bản hiện tại có 53 câu đưa ra kết quả ngay và không có nút mở rộng, 45 câu có nút và 22 câu trả rỗng mà không có nút. Phép thử chính bảo toàn thứ hạng của 53 câu đầu. Nó cho phép chủ động tìm theo nghĩa ở cả 45 câu có nút lẫn 22 câu trước đây trả rỗng.

Để kiểm tra ảnh hưởng của thay đổi này, nhóm dùng lại đúng thứ hạng đã ghi và chỉ thay kết quả của 45 câu **vốn có nút**. Khi đó, cấu hình thêm embedding đạt **88/120** và cấu hình có xếp hạng lại đạt **93/120**. Cả hai có **14/26** câu không có đáp án nhận gợi ý sai, ngang bản hiện tại. Cả bốn gợi ý sai phát sinh trong phép thử chính đều đến từ việc mở rộng phạm vi sang 22 câu vốn trả rỗng. [Trạng thái nút theo câu](../scenario-matrix/results-windows.json) · [Kết quả sau khi thay cách xếp hạng](results-windows.json)

## Mô hình và cách chấm

Trước khi chấm, dịch vụ `SearchService` thực chạy trên PostgreSQL QA và tái hiện đúng thứ hạng của cả 120 câu ở hai chế độ. Nhóm dùng 51 câu **riêng** trên 36 ghi chú cũ để chốt ngưỡng hiển thị kết quả. Bộ hiệu chỉnh có 36 câu dương và 15 câu âm. Tiêu chí chọn ngưỡng là trung bình của tỷ lệ đúng hạng 1 trên các câu dương và tỷ lệ trả rỗng trên các câu âm. Hai ngưỡng đã chốt là cosine **0,48** cho embedding và logit **−2,0** cho bộ xếp hạng lại. [Mã phép thử đã khóa](https://github.com/cavoixanh638/kho-tri-thuc/commit/7150b74c87bc2614c2619edbfe1107281c45962a) · [Ngưỡng khóa trước lượt chấm](https://github.com/cavoixanh638/kho-tri-thuc/commit/c2369185363b8ff8550a656a761f6e05118d3197) · [Kết quả hiệu chỉnh](calibration-windows.json)

Ứng viên đều thuộc phạm vi chủ kho, bộ lọc và trạng thái của truy vấn. Bộ thử ghép tiêu đề, mô tả và nội dung ghi chú, lấy 12 ứng viên vector gần nhất trong phạm vi, gộp với tối đa 5 kết quả tìm từ khóa bằng Reciprocal Rank Fusion với hằng số 60. Cấu hình thứ hai lọc ứng viên theo cosine rồi giữ năm mục. Cấu hình thứ ba chấm lại tối đa tám ứng viên đầu bằng cặp câu hỏi và ghi chú, lọc theo logit, rồi giữ năm mục. Dữ liệu đầu vào cho hai mô hình nằm trên máy Windows.

Nhóm dùng đồ thị ONNX FP32 do AITeamVN phát hành, lấy vector CLS 1.024 chiều và chuẩn hóa L2. Bộ xếp hạng lại dùng bản ONNX lượng tử hóa 8 bit của BGE. Hai mô hình chạy bằng ONNX Runtime CPU với 4 luồng và giới hạn 512 token mỗi đầu vào. Tệp tin được ghim theo phiên bản và kiểm tra mã băm sau khi tải. [Vietnamese Embedding v2](https://huggingface.co/AITeamVN/Vietnamese_Embedding_v2/tree/18b44161e041bf1d3a333ab5144b5b7b93f914d2) · [BGE reranker gốc](https://huggingface.co/BAAI/bge-reranker-v2-m3) · [Bản ONNX đã dùng](https://huggingface.co/onnx-community/bge-reranker-v2-m3-ONNX/tree/6f5ff65298512715a1e669753bc754d2bc8f367b)

## Thời gian tìm trên 10.000 ghi chú

Trên Windows với CPU Intel Core i5-12400, ONNX Runtime 1.32.0 dùng 4 luồng. Lần tạo mới 10.000 vector 1.024 chiều theo lô 32 ghi chú mất **12 phút 40 giây**, sau khi mô hình đã nạp. Dữ liệu vector float32 chiếm **40.960.000 byte**, khoảng 39,1 MiB. Cùng một bộ gồm 20 ghi chú đích tự soạn và 9.980 ghi chú được sinh từ mẫu tiếng Việt đã được đưa vào cả PostgreSQL QA và chỉ mục vector. [Bộ ghi chú và truy vấn](scale.py) · [Kết quả tạo chỉ mục](scale-build-windows.json)

| Thời gian tính từ khi nhận truy vấn | Trung vị | P95 |
| --- | ---: | ---: |
| Đến khi SearchService trả kết quả từ khóa, gồm lượt mở rộng nếu có nút | 1,191 s | 1,268 s |
| Đến khi gộp xong ứng viên từ khóa và embedding | 1,247 s | 1,326 s |
| Đến khi xếp hạng lại xong tám ứng viên | 1,589 s | 1,680 s |

Nhóm đo tuần tự 20 truy vấn khác nhau, mỗi truy vấn một lần sau ba lượt làm nóng. Từng truy vấn được mã hóa lại. Ở P95, riêng mã hóa câu hỏi mất 72,69 ms, quét toàn bộ vector và lấy các ứng viên đầu mất 1,66 ms, còn xếp hạng lại mất 381,66 ms. Các mốc tích lũy trong bảng được tính từ từng lượt đo. P95 là giá trị thứ 19 trong 20 lượt đã sắp theo thời gian.

Mỗi truy vấn ở phép đo độ trễ đều chạy đến hết bước xếp hạng lại. Có 19/20 ghi chú đích lọt vào tám ứng viên và 17/20 đứng đầu sau khi xếp hạng. Phép đo dùng ghi chú ngắn tự soạn và chạy nối tiếp trong một tiến trình đã nạp mô hình. Thời gian người dùng chờ trong trình duyệt cần đo riêng. Dữ liệu trong PostgreSQL QA đã được hoàn tác và kiểm tra lại sau khi đo. [Thời gian và thứ hạng theo từng truy vấn](scale-windows.json)

## Chạy lại từ gốc repo

Dùng Python của môi trường thử có Django, driver PostgreSQL của backend, NumPy, ONNX Runtime CPU, tokenizers và requests. Trỏ các biến kết nối Django vào cơ sở dữ liệu QA trống `kt_eval_edge_pairs` đã migrate. Đo trên kho khác hoặc mô hình khác sẽ cho kết quả khác. [Hướng dẫn PostgreSQL QA](../README.md#chạy-từ-gốc-repo) · [Phiên bản thư viện thực đo](results-windows.json)

```powershell
$pilot = 'evals/vietnamese-journeys/semantic-pilot'
$run = Join-Path $env:TEMP ('kt-semantic-' + [guid]::NewGuid().ToString('N'))
$models = Join-Path $run 'models'
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_DB = 'kt_eval_edge_pairs'
$env:KT_EVAL_ALLOW_DISPOSABLE = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:TOKENIZERS_PARALLELISM = 'false'
python "$pilot/fetch_models.py" --directory $models
python "$pilot/references.py" --output "$run/lexical.json"
python "$pilot/pilot.py" calibrate --models $models --reference "$run/lexical.json" --calibration "$run/calibration.json"
python "$pilot/pilot.py" evaluate --models $models --reference "$run/lexical.json" --calibration "$run/calibration.json" --output "$run/quality.json"
python "$pilot/scale_windows.py" build --models $models --index "$run/10k.npy" --output "$run/build.json"
python "$pilot/scale_windows.py" measure --models $models --index "$run/10k.npy" --output "$run/latency.json"
```

Hai phép đo dùng PostgreSQL đều hoàn tác ghi chú và kiểm tra kho trống sau khi chạy. Chỉ mục vector 10.000 ghi chú nằm trong tệp cục bộ. Các số liệu ở đây chỉ áp dụng cho nội dung tự soạn và xử lý trong dịch vụ. Trải nghiệm người dùng trên giao diện cần đo riêng.
