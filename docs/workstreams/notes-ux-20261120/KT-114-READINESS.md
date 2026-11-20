# KT-114 — CORE GATE: kiểm chứng lưu trữ, xử lý nguồn, 10.000 mục và phục hồi

**Ưu tiên:** GATE an toàn *trước phát hành mở rộng*; có thể chạy song song với UI PoC cô lập. **Trạng thái:** READY_TO_ASSIGN / NOT_RUN. **Không thay UI chỉ để đạt gate.**

## Nhiệm vụ thực thi

1. Đọc `CURRENT_STATE.md` và evidence Windows/Drive thật, tách **đã có live proof nhỏ** khỏi **10.000 Item/100+ GB** còn NOT_RUN. Kiểm `CaptureService`, `StorageLocation`, `reconcile_drive`, backup/restore, yt-dlp/worker và tìm kiếm.
2. Tạo **harness QA cô lập** cho corpus tổng hợp **10.000 Item**, cây nhiều tầng, một Item nhiều nhánh, Source/DerivedContent/RelatedItem/CaptureEvent gắn version. Không đưa 10.000 Item giả vào database đang phục vụ người dùng. Ghi cách seed/cleanup DB tạm và công thức đếm/tổng.
3. Kiểm integrity: `COUNT(DISTINCT item_id)` khớp số duy nhất; gửi URL thật mới → Event mới, retry cùng idempotency key → Event cũ; pinned không bị ghi đè; restore từng Item/Event/source/version/locator/Drive mapping. Nếu thiếu điều kiện chạy PostgreSQL/Drive, giữ NOT_RUN rõ từng lớp.
4. Tạo bộ test các trạng thái lỗi: timeout, 429, retry, upload/Drive chưa xác minh, file inaccessible, metadata-only, video thiếu phụ đề; không tuyên bố worker đã hiểu hoặc lưu MP4 khi chưa có byte/hash. Kiểm nguồn FB/TikTok/YT trên nguồn công khai **nếu quyền và môi trường cho phép**, không vượt chống truy cập.
5. Lập danh sách hạn chế: OAuth khi đổi host/client/project; Google Drive quota/tệp lớn; phát MP4/thumbnails; Android thiết bị thật (KT-117); hiệu năng 10k/100GB; kế hoạch đo dần không yêu cầu chạy media hàng trăm GB ngay.

## Phạm vi file

- **Được sửa/tạo:** `tools/readiness/*`, `evals/readiness/*`, báo cáo test không nhạy cảm cùng thư mục task, test mới dưới tên KT-114.
- **Chỉ đọc:** `apps/backend/ingestion/*`, `storage/*`, `processing/*`, `catalog/*` và tài liệu hệ thống. Nếu có bug core, ghi minimal reproduction và file cần sửa; thực hiện trên PR fix riêng có phân quyền, không ghi đè luồng khác.
- Không tải file cá nhân/đăng ký dịch vụ/đổi quyền Google. Không tạo DB giả trên production.

## Acceptance/định lượng

| Ca | Cách tính và chứng cứ | Gate |
| --- | --- | --- |
| Unique item theo view/nhánh | `distinct_item_ids = count(unique(id))`; chênh lệch = `count(displayed_unique_ids) - count(expected_unique_ids)` | 0 trên fixture 10k |
| Lịch sử gửi và retry | `events = count(CaptureEvent)` trước/sau; gửi lại 2 lần thật → +2, một retry cùng key → +0 | Đạt trong DB test |
| Backup/restore | So sánh count và hash theo Item/Event/Asset/mapping; SHA file mẫu trước/sau | Không mất byte/ID trong phạm vi đã kiểm |
| Auto-group curated | `false_auto_assign_rate = wrong_auto_assignments / audited_auto_assignments`; nếu mẫu đánh giá rỗng → NOT_RUN | Không sửa pinned; ghi precision có nhãn |
| Tải và phát media | Hash SHA-256 readback + phát/xem được trên hệ cần hỗ trợ | Không suy khi chỉ mock |

**Nếu 100 GB/Drive thực hoặc Android không có quyền thử:** ghi NOT_RUN, không giả “0 lỗi” hay PASS. Bất kỳ lỗi mất dữ liệu hoặc media nguồn phải có **blocker** ưu tiên hơn UX. Deliverable: script chạy được + hướng dẫn lệnh + kết quả có SHA + PR, không chỉ checklist.
