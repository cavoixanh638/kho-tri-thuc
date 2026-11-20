# Sơ đồ tài liệu — Kho Tri Thức

Trang điều hướng này chỉ **trỏ tới nguồn chuẩn**; không viết lại toàn bộ kế hoạch.

| Cần biết | Đọc tài liệu |
| --- | --- |
| Mục tiêu, phạm vi MVP, lựa chọn đã chốt | [MASTER_PLAN.md](MASTER_PLAN.md) |
| **Tiếp nhận URL/ghi chú, lịch sử bất biến, tự phân nhóm và mục liên quan** | **[CAPTURE_AND_ORGANIZE.md](CAPTURE_AND_ORGANIZE.md)** |
| Mô hình dữ liệu, Drive/PostgreSQL/API/search, cách mở rộng | [ARCHITECTURE_AND_DATA.md](ARCHITECTURE_AND_DATA.md) |
| KT-xxx, phụ thuộc, điều kiện PASS và U01–U23 | [ROADMAP_AND_TESTS.md](ROADMAP_AND_TESTS.md) |
| **Giao AI sau nghiên cứu 17 ứng dụng (KT-114–KT-121), ranh giới file, prompt ngắn** | **[workstreams/notes-ux-20261120/INDEX.md](workstreams/notes-ux-20261120/INDEX.md)** |
| **Nguồn thẩm định và các sửa sai của G00** | [PR #47 — báo cáo thẩm định và tổng hợp, chưa merge](https://github.com/cavoixanh638/kho-tri-thuc/pull/47) |
| **Trạng thái hiện tại, test thực sự chạy, blocker, việc kế tiếp** | [CURRENT_STATE.md](CURRENT_STATE.md) |
| **Quy tắc đặt file và ranh giới Git/Drive/PostgreSQL/cache** | [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md) |
| Cây thư viện, bài văn bản, nguồn minh họa và chép lời Windows | [operations/KNOWLEDGE_TREE.md](operations/KNOWLEDGE_TREE.md) |
| Quy tắc và thứ tự đọc cho Codex/AI | [../AGENTS.md](../AGENTS.md) |
| Tổng quan cho người dùng | [../README.md](../README.md) |

## Đọc nhanh cho người mới hoặc AI

1. Đọc `../README.md` và `../AGENTS.md`.
2. Đọc `CURRENT_STATE.md` để không lẫn kế hoạch với kết quả chạy thật.
3. Đọc `MASTER_PLAN.md`, **`CAPTURE_AND_ORGANIZE.md`** khi làm tiếp nhận/phân nhóm/tương tự, rồi phần liên quan của `ARCHITECTURE_AND_DATA.md`.
4. Trước khi tạo/move file, đọc `REPOSITORY_LAYOUT.md`.
5. Nhận đúng task và kiểm tiêu chí tại `ROADMAP_AND_TESTS.md`; với KT-114–121, đi qua `workstreams/notes-ux-20261120/INDEX.md` và file task, đối chiếu code/test mới nhất. Mỗi AI ghi kết quả trong PR; G00 cập nhật `CURRENT_STATE.md` sau review/merge để tránh xung đột.

## Tài liệu sẽ bổ sung khi có bằng chứng

- `operations/LOCAL_SETUP.md`: chỉ lập sau khi KT-001 có lệnh cài/chạy/test thật trên máy đích.
- `operations/BACKUP_RESTORE.md`: chỉ lập sau KT-008 khi backup và restore đã thực thi kiểm chứng.
- `FEATURE_MAP.md`/`REPO_MAP.md`: chỉ khi mã nguồn đã đủ lớn khiến việc truy trách nhiệm khó; không tạo file trống.
- `evals/`: chỉ khi thực sự có tập mẫu/runner/báo cáo chất lượng, phân biệt với `tests/`.

**Quy tắc của QLVB được kế thừa:** hiện trạng không thay thế kế hoạch, nghiên cứu không tự trở thành quyết định, mã nguồn trong Git không chứng minh runtime đã chạy; một sự thật chỉ có một nơi chuẩn.
