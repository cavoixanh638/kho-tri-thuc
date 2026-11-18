# Đánh giá tạm cho quy tắc tổ chức

Tập 40 mục do model soạn, gồm 20 nội dung và 20 lượt tạo Item riêng có cùng văn bản. Nhãn kỳ vọng được kiểm theo hợp đồng rule. Đây là fixture tổng hợp để phát hiện lỗi tích hợp, có trạng thái `PROVISIONAL_MODEL_AUTHORED_FIXTURES`. KT-107 với 30–50 nội dung thực được người dùng đánh giá còn cần thực hiện.

Chạy từ `apps/backend` với cấu hình PostgreSQL của môi trường thử.

```powershell
python manage.py shell -c "import runpy; runpy.run_path('../../evals/organization/run.py', run_name='__main__')"
```

Runner tạo tài khoản/dữ liệu tổng hợp trong transaction và rollback toàn bộ sau khi đo. `results.json` chứa số đo trên PostgreSQL 18.4 Windows. Kết quả được tính lại bằng runner.

Lượt ngưỡng đầu 4 từ chung và Jaccard 1.0 cho 72 liên kết, precision 20/72 trên các cặp kỳ vọng. Các tiêu đề ngắn lặp lại gây false positive. Ngưỡng 6 từ chung và Jaccard 1.0 cho 20/20 liên kết kỳ vọng trong tập hiện tại. Runtime dùng ngưỡng thận trọng này với nguyên nhân được lưu trên RelatedItem. Recall với nội dung diễn đạt bằng từ khác cần đo riêng. Các số này chỉ mô tả fixture, chưa xác nhận chất lượng trên kho thực.

Tên nhóm 'Giáo dục' có hai token nên được gán bởi rule cụm từ đã thiết kế. Nhãn kỳ vọng ban đầu cho hai fixture tương ứng đã được điều chỉnh để khớp hợp đồng đó. Tên Project vẫn cần một dòng khai báo 'Dự án:' hoặc 'Project:' trong ghi chú.
