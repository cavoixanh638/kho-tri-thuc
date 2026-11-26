# Tìm lại ghi chú dễ nhầm

Bộ thử có 10 ghi chú tiếng Việt tự soạn và 21 câu hỏi. Trong đó có 14 câu có một đáp án, hai câu yêu cầu tìm cả cặp và năm câu không có nội dung phù hợp. Các ghi chú đối chiếu lịch cũ/mới, mượn/trả, trước/sau và hai đối tượng tương tự. Đáp án do tác nhân soạn và khóa trong commit `4cacebb4d40b25bbe93b334765e87025968ba1a0` trước khi chạy bộ thử.

## Kết quả ngày 26/11/2026

Mỗi ô đếm số câu thỏa điều kiện ở cột đầu. Ở lượt mở rộng, phép đo chọn **Tìm gần đúng** nếu có nút và đọc lại thứ tự của danh sách.

| Điều kiện | Bản trước · lượt đầu | Bản trước · có mở rộng | Bản mới · lượt đầu | Bản mới · có mở rộng |
| --- | ---: | ---: | ---: | ---: |
| Một đáp án chấp nhận được đứng đầu | 3/16 | 15/16 | 3/16 | **16/16** |
| Đủ mọi đáp án chấp nhận được trong 5 mục đầu | 2/16 | 15/16 | 2/16 | **16/16** |
| Câu không có đáp án nhưng có kết quả | 2/5 | 4/5 | 2/5 | **4/5** |

Câu “Lịch thứ hai: việc trả máy trình chiếu sau buổi thơ.” trước đây trả rỗng, kể cả khi người đọc muốn mở rộng. Sau khi sửa cách xử lý dấu hai chấm trong câu văn, nút **Tìm gần đúng** đưa ghi chú bàn giao máy lên đầu. [Kết quả trước ở `d1e47e8`](baseline.json) · [Kết quả sau ở `ba1e751`](candidate.json)

Hai câu âm vẫn có kết quả ngay lượt đầu. “Lịch tưới vườn chung tháng Tư” trả các lịch tháng Hai và tháng Ba. “Ghi chú dán thẻ giá vào chén sau khi cổng đóng” trả bài dọn sân, trong đó người làm **bóc** thẻ sau khi đóng cổng. Nhiều từ và cụm đứng cạnh nhau cùng khớp dù bài sai tháng hoặc sai hành động. Ưu tiên kiểm hai tình huống này khi thay đổi cách xếp hạng. [Câu hỏi và ghi chú gốc](fixture.json)

## Chạy lại

Dùng Python của backend với PostgreSQL QA cục bộ. Tạo và migrate DB trống `kt_eval_edge_pairs` theo [hướng dẫn chung](../README.md#chạy-từ-gốc-repo). Runner kiểm tra tên DB, dữ liệu trống và cây mã backend, gọi trực tiếp `SearchService`, rồi rollback dữ liệu thử. Có thể truyền `--repo` để chỉ sang worktree khác.

```powershell
$env:POSTGRES_DB = 'kt_eval_edge_pairs'
$env:KT_EVAL_ALLOW_DISPOSABLE = '1'
python apps/backend/manage.py migrate --noinput
python evals/vietnamese-journeys/confusable-cases/run.py --expected-source HEAD --report pairs.json
```

Với mỗi câu dương, báo cáo tính riêng có đáp án chấp nhận được ở hạng 1, có ít nhất một đáp án trong top 5 và có đủ đáp án trong top 5. Sau khi chọn gợi ý, dùng kết quả mở rộng nếu giao diện có nút và giữ kết quả ban đầu trong các ca còn lại. Với câu âm, báo cáo đếm số câu có kết quả, tổng số kết quả và số gợi ý thực sự xuất hiện sau khi mở rộng. Bộ thử đo hành vi dịch vụ trên ghi chú văn bản trong một kho nhỏ. Người dùng chưa thử thao tác này qua trình duyệt hoặc trên kho thực.
