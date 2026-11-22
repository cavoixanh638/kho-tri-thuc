## Mục tiêu và đối chiếu kế hoạch (bắt buộc)
- **Mã nhiệm vụ KT/Pxx:** 
- **Mốc A/B/C/D (MASTER_PLAN v4.7):**
- **Yêu cầu gốc được phục vụ:** 
- **Thay đổi phạm vi:** Không / Có (mô tả và nguồn quyết định):
- **Trạng thái trước → sau:** 

## Mã nguồn và kiểm chứng
- **Nhánh base + SHA:** 
- **Code SHA / Tested SHA:** 
- **Các tệp/migration/API thay đổi:** 
- **Môi trường, tập dữ liệu, câu lệnh kiểm thử:** 
- **PASS/FAIL/NOT_RUN từng cổng:** G1 dữ liệu; G2 UAT; G3 chất lượng; G4 quy mô; G5 vận hành
- **Kết quả số (tử số/mẫu số/công thức + ca bỏ qua, lý do):** 
- **Bằng chứng:** Actions job + step (không chỉ badge xanh), artifact/screenshot/log/JSON redacted
- **Các ca chưa thử hoặc yêu cầu quyền/chi phí:** 
- **Risk/rollback:** 
- **NEXT / nhánh, PR phụ thuộc:** 

## Checklist trước khi đề xuất tích hợp
- [ ] Đã đọc MASTER_PLAN, ROADMAP_AND_TESTS, CURRENT_STATE và `docs/operations/RELEASE_READINESS_20261122.md`
- [ ] Đã rà lại HEAD của main/base/PR liên quan, diff `ahead/behind` và các migration có thể xung đột
- [ ] Không giả định `CI SUCCESS` đồng nghĩa P08/P15/Drive/Gemini đã nghiệm thu
- [ ] Không sửa tài liệu kế hoạch để hợp thức hóa code chưa đạt; mọi NOT_RUN có lý do
- [ ] Không commit dữ liệu cá nhân, OAuth/API key, không gọi AI trả phí khi chưa có quyền
- [ ] Không tự merge/deploy hoặc chạy test ngoài môi trường cách ly
- [ ] G00 nhận báo cáo, cập nhật CURRENT_STATE sau review/tích hợp
