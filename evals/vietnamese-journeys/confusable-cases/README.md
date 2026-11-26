# Tìm lại ghi chú dễ nhầm

Bộ thử có 10 ghi chú tiếng Việt tự soạn và 21 câu hỏi. Trong đó có 14 câu có một đáp án, hai câu yêu cầu tìm cả cặp và năm câu không có nội dung phù hợp. Các ghi chú đối chiếu lịch cũ/mới, mượn/trả, trước/sau và hai đối tượng tương tự. Đáp án do tác nhân soạn và khóa trong commit `4cacebb4d40b25bbe93b334765e87025968ba1a0` trước khi chạy bộ thử.

Dùng Python của backend với PostgreSQL QA cục bộ. Tạo và migrate DB trống `kt_eval_edge_pairs` theo [hướng dẫn chung](../README.md#chạy-từ-gốc-repo). Runner kiểm tra tên DB, dữ liệu trống và cây mã backend, gọi trực tiếp `SearchService`, rồi rollback dữ liệu thử. Có thể truyền `--repo` để chỉ sang worktree khác.

```powershell
$env:POSTGRES_DB = 'kt_eval_edge_pairs'
$env:KT_EVAL_ALLOW_DISPOSABLE = '1'
python apps/backend/manage.py migrate --noinput
python evals/vietnamese-journeys/confusable-cases/run.py --expected-source d1e47e8 --report pairs.json
```

Với mỗi câu dương, báo cáo tính riêng có đáp án chấp nhận được ở hạng 1, có ít nhất một đáp án trong top 5 và có đủ đáp án trong top 5. Sau khi chọn gợi ý, dùng kết quả mở rộng nếu giao diện có nút và giữ kết quả ban đầu trong các ca còn lại. Với câu âm, báo cáo đếm số câu có kết quả, tổng số kết quả và số gợi ý thực sự xuất hiện sau khi mở rộng. Bộ thử đo hành vi dịch vụ trên ghi chú văn bản trong một kho nhỏ. Người dùng chưa thử thao tác này qua trình duyệt hoặc trên kho thực.
