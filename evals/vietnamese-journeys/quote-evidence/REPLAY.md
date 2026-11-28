# Đo kiểm trích dẫn cho tìm kiếm tiếng Việt

Runner dùng Django test client đăng nhập qua `GET/POST /api/v1/session` với CSRF thật. Từng ca gọi tuyến `GET /api/v1/search` mặc định và chỉ gửi `expand=true` khi phản hồi đầu tiên có `can_expand`. Phép đo bao gồm xử lý API và lần gọi reader loopback nếu được kích hoạt. Nó không đo mạng trình duyệt hoặc thời gian render.

`120` dùng scenario matrix, `400` dùng memory-400, `48` dùng holdout và `36` dùng bộ đối chiếu câu xác nhận, bác bỏ và thiếu bằng chứng. Các ghi chú đều là dữ liệu tổng hợp. Gold tìm kiếm giữ nguyên từ fixture. Nhãn hỏi đáp và đoạn trích đối chiếu nằm trong `polarity-audit.json` hoặc `contrast-36.json`. Ca không có nhãn hỏi đáp vẫn có kết quả tìm kiếm. Đoạn trích đạt nếu là nguyên văn từ đúng trường của đúng nguồn và trùng hoặc chứa/nằm trong đoạn đối chiếu đã gắn nhãn.

## Chuẩn bị

Xem [Chuẩn bị máy localhost](LOCAL_SETUP.md) để cài phụ thuộc Python, migrate một PostgreSQL loopback chuyên dùng và khởi động reader. Thực thi lệnh từ gốc checkout có runner và bốn bộ fixture. Định vị lệnh Python trong môi trường ảo đã cài các phụ thuộc của backend.

Có thể kiểm tra riêng fixture mà chưa cần PostgreSQL và model.

```sh
python evals/vietnamese-journeys/quote-evidence/run.py --suite 48 --validate
```

## Chạy thử nghiệm

`--mode control` giữ xếp hạng mở rộng của ứng dụng và tắt reader. `--mode feature` bật reader, với cùng BGE và chế độ ứng viên của control. Chạy hai mode theo cùng thứ tự, tuần tự. Muốn đo backend trước khi tích hợp thì thêm `--backend <checkout>` và `--expected-source <commit>` vào lệnh control. Runner yêu cầu cây mã backend sạch và khớp commit đã nêu. BGE được xác minh theo SHA-256 và làm nóng trước khi ghi thời gian.

Windows PowerShell. Thay `$bge` bằng thư mục BGE đã xác minh, sau đó dùng biến môi trường PostgreSQL từ bước chuẩn bị.

```powershell
$runner = 'evals/vietnamese-journeys/quote-evidence/run.py'
$bge = Join-Path $HOME 'kt-eval-models/bge-reranker-v2-m3'
$env:KT_EVAL_ALLOW_DISPOSABLE = '1'
$revision = '4edb920b6f14e3b9284d4502a6485103d72cde05'
foreach ($suite in @('120','400','48','36')) {
    python $runner --suite $suite --mode control --bge $bge --energy --output "control-$suite.jsonl"
    if ($LASTEXITCODE -ne 0) { throw "Control $suite failed" }
    python $runner --suite $suite --mode feature --bge $bge --energy --output "feature-$suite.jsonl" `
        --reader-url http://127.0.0.1:19587/v1/chat/completions `
        --reader-model qwen3-4b-instruct-2507-q4_k_m --reader-revision $revision
    if ($LASTEXITCODE -ne 0) { throw "Feature $suite failed" }
}
```

Linux.

```sh
set -e
export KT_EVAL_ALLOW_DISPOSABLE=1
runner=evals/vietnamese-journeys/quote-evidence/run.py
bge="$HOME/kt-eval-models/bge-reranker-v2-m3"
revision=4edb920b6f14e3b9284d4502a6485103d72cde05
for suite in 120 400 48 36; do
  python "$runner" --suite "$suite" --mode control --bge "$bge" --output "control-$suite.jsonl"
  python "$runner" --suite "$suite" --mode feature --bge "$bge" --output "feature-$suite.jsonl" \
    --reader-url http://127.0.0.1:19587/v1/chat/completions \
    --reader-model qwen3-4b-instruct-2507-q4_k_m --reader-revision "$revision"
done
```

Bỏ `--energy` trên máy không có bộ đếm. Tuỳ chọn này đo tổng điện năng của gói xử lý Intel trong khoảng thời gian dành cho click, gồm iGPU và phần điện năng do tiến trình khác gây ra. Hai lần lấy mẫu có ghi chi phí lấy mẫu riêng. Đơn vị Wh là chênh tích lũy pWh chia cho 10¹². Giá trị bị thiếu, bộ đếm giảm hoặc khoảng lấy mẫu sai có trạng thái riêng. Số đo tại ổ cắm và giá điện cần một phép đo tại ổ cắm và biểu giá riêng. Phí API từ xa là 0 USD với reader mạng cục bộ này. [Microsoft Energy Metering Interface](https://learn.microsoft.com/en-us/windows-hardware/drivers/powermeter/energy-meter-interface).

## Đọc kết quả

File JSONL có dòng metadata, một dòng mỗi ca và dòng `complete` sau khi đã rollback dữ liệu seed. Các dòng dữ liệu thử được rollback, trong khi sequence PostgreSQL có thể tăng qua mỗi lượt. Dùng ID fixture trong báo cáo để ghép cặp. Runner tạo file mới và giữ các dòng đã ghi nếu dừng giữa chừng. Chỉ lấy hai lượt có dòng `complete` để tổng hợp đầy đủ.

- `default` và `click` chứa độ trễ API tính bằng ms, thời gian CPU của tiến trình Django client, ID fixture và phản hồi API. `click` rỗng khi không có nút.
- `click.page.quote_check` chứa trạng thái, độ trễ reader và token prompt/completion khi reader cung cấp. Trạng thái `checked` với kết quả rỗng biểu thị reader đã chạy và không chọn nguồn.
- `answer_gold` và `gold_anchors` chứa nhãn hỏi đáp và nguồn đối chiếu. `click.evidence` ghi câu trả lời, nguyên văn và phần khớp với đoạn đối chiếu. So sánh hai lượt theo `id`, giữ `search_verdict` và `gold_pass` là hai tiêu chí khác nhau.
- `click.energy` ghi Wh của gói xử lý nếu bộ đếm đọc được. Thời gian CPU của tiến trình chạy runner chỉ phản ánh tiến trình đó, còn độ trễ API bao gồm thời gian chờ reader.
