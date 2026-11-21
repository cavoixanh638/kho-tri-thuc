# KT-130 — Deferred/Conditional Capability Register

**Phân loại:** CONDITIONAL / NOT CODE. **Ngày lập:** 20/11/2026. **Trạng thái:** SPEC_READY / IMPLEMENTATION_NOT_RUN. **Nguồn:** [G00 traceability audit](G00-FEATURE-TRACEABILITY.md), PR #30–47, PR #57. Đây là đề xuất có thể giao, **không phải tính năng đã triển khai**.

**Mục đích:** không đánh rơi các điểm tốt còn lại từ 17 nghiên cứu, nhưng cũng không bắt hệ thống làm mọi thứ cùng lúc.

| Năng lực | Nguồn | Điều kiện mở | Lý do chưa triển khai |
| --- | --- | --- | --- |
| Source-scoped notebook, research compare, FAQ có citations | OneNote, Gemini Notebook, Granola | Người dùng cần thực hiện nghiên cứu nhiều nguồn trên 10–20 Item công khai; có source-set read-only trước AI | Chưa cần provider và chưa có benchmark câu trả lời |
| Whiteboard/Canvas-lite, graph visualization | AFFiNE, Heptabase, Obsidian | Người dùng cần sắp luận điểm bằng không gian 2D sau KT122/123/116 PASS | Chi phí UX và state maintenance cao, editor + folders quan trọng hơn |
| OCR ảnh/PDF scan tiếng Việt | Keep, Apple Notes, Evernote | Corpus ≥30 trang/ảnh scan không có text và mục tiêu CER/WER/latency rõ | Không tự bật AI/cloud OCR hàng loạt |
| Voice quick inbox/timed meeting annotation/reminder | Keep, OneNote, Superpowered, Granola | Có nhu cầu ghi âm/nhắc việc trực tiếp trong Kho Tri Thức, liên thông app ghi họp riêng | Không xây lại recorder/notifications không được giao |
| Semantic/hybrid search | Evernote, Mem, Capacities, Reflect | 50–100 truy vấn Việt có gold, recall tăng rõ so FTS, kiểm phí/quyền | Không thêm vector/embedding khi FTS chưa được đo |
| Rich BlockSuite/ProseMirror or CRDT collaboration | Notion, AFFiNE, Coda | Markdown editor chứng minh chưa đáp ứng use case, có PoC roundtrip/lossless + license | Không fork, không khóa định dạng |
| Multi-device true offline sync | Obsidian, Reflect, AFFiNE | Người dùng cần edit offline nhiều thiết bị, nghiên cứu conflicts và ownership | Dễ gây xung đột/mất note; offline receipt không giả server ack |
| Automation multi-app/AI agents | Lark/Coda/Tana/Mem | Quy trình thực tế có mẫu lặp và quyền provider rõ | Tránh over-engineer |

**Mọi mục có ID, nguồn, điều kiện mở, lý do hoãn.** Không được xóa khỏi sổ tính năng mà không có quyết định. Không tự bật API AI tính phí, Mem/Superpowered làm dịch vụ gốc, hoặc những bản beta chưa được xác nhận. Khi có lệnh mới, mở task cụ thể và test/consent, không đổi kiến trúc trước.

**Bàn giao:** Mỗi agent đọc AGENTS.md, CURRENT_STATE.md, code HEAD và các PR đang mở, ghi Code SHA/Tested SHA, lệnh kiểm, PASS/FAIL/NOT_RUN, dependency, rollback; commit/push/PR riêng. Không merge hay deploy. Không được tự sửa hợp đồng data gốc, CURRENT_STATE đồng thời hoặc dữ liệu sản xuất.
