# Điều phối triển khai KT-114–KT-121

Baseline: `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b` trên main.
Người dùng giao toàn bộ KT-114–121, làm theo phụ thuộc, phần độc lập song song;
commit/push/PR, **không merge, không deploy**. G01–G17/G00 nghiên cứu giữ nguyên.

| Task | Owner / branch | Trạng thái |
| --- | --- | --- |
| KT-114 | root / `codex/kt-114-readiness` | Harness cô lập đã viết, TEST_PENDING |
| KT-115 | agent kt115 / `codex/kt-115-editor` | IN_PROGRESS, editor A không thêm dependency |
| KT-116 | agent kt116 / `codex/kt-116-source-locators` | IN_PROGRESS, schema read/provenance và adapter |
| KT-117 | agent kt117 / `codex/kt-117-quick-capture` | IN_PROGRESS, fixture/draft/ACK |
| KT-118 | root điều phối, sau gate KT-114 | NOT_STARTED |
| KT-119 | giao khi slot trống | NOT_STARTED |
| KT-120 | root điều phối | NOT_STARTED; user đã giao, provider/budget chưa có, chỉ PoC fixture/no-provider |
| KT-121 | giao khi slot trống | NOT_STARTED; user đã giao template tùy chọn |

Worktree mỗi task riêng, cùng parent temp ngoài production; writer độc quyền.
Không sửa shared runner/api/styles/CURRENT_STATE trong các PR song song.
Test mới chạy tường minh; ghi owner/Code SHA/Tested SHA/CI trong PR mỗi task.
Backend test dùng database tên riêng ở QA cluster 62224, không dùng chung
`test_postgres`. Windows production 8009/54329 và OAuth/Drive không bị sửa.

Tiếp: chạy safety + corpus 10k/restore KT114; giao KT118/119/120/121 khi scope
không phụ thuộc đã đủ; cập nhật tracker theo mốc và đính link PR. Mục tiêu là
PR có mã và bằng chứng, không tuyên bố main hay thiết bị đã nghiệm thu.
