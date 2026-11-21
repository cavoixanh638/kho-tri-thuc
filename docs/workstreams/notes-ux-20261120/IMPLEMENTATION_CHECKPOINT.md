# Điều phối KT-114–KT-121 — mã và PR, không merge

Baseline `7044b4a0f50a7c831a391f27b1f90cc4aaa21d8b` trên main. Người dùng giao
KT-114–121, phần độc lập song song; commit/push/PR, **không merge/deploy**.
G01–G17/G00 nghiên cứu không đổi. Đây là checkpoint các PR đang mở, không thay
CURRENT_STATE của ứng dụng đã triển khai. Main và Windows production không đổi.

| Task | PR / nhánh | Code/Tested SHA | Kết quả thực sự đã chạy |
| --- | --- | --- | --- |
| KT-114 | [48](https://github.com/cavoixanh638/kho-tri-thuc/pull/48) `codex/kt-114-readiness` | `d38287ed73f31dab9984fb508d10d111acdb67d1` | 10k PostgreSQL,138 nhánh,221 page không lệch/trùng; restore15 collection full-row hash; backend211/safety3; CI44710609558 PASS |
| KT-115 | [51](https://github.com/cavoixanh638/kho-tri-thuc/pull/51) `codex/kt-115-editor` | `4aa645f8ec7f896f28135d9effa79ad7bd064db6` | Editor47 new+19 legacy/build;40 raw-byte fixtures; Chromium keyboard/reload/responsive; CI44711974025 PASS |
| KT-116 | [49](https://github.com/cavoixanh638/kho-tri-thuc/pull/49) `codex/kt-116-source-locators` | `70120713530151bc27b9d45ba4d50a8cf876cd40` | 30 mapping/10 new UI/19 legacy/10 backend/build;40 WAV/VP8 browser seek marks; CI44712705482 PASS |
| KT-117 | [50](https://github.com/cavoixanh638/kho-tri-thuc/pull/50) `codex/kt-117-quick-capture` | app `3b777a46f18cb0a8107d1f195a58936ea0421360`, packaging `16925a09aaade25eb59ff2f04e6cb9bc2310cee3` | 45 new UI/19 legacy/build;30 raw/receipt/retry DB cases; Chromium3 widths; fixture Docker path fix; CI44712852887 PASS |
| KT-118 | [52](https://github.com/cavoixanh638/kho-tri-thuc/pull/52) `codex/kt-118-library-views` | `a20072e46a4d4111c7355bb1007b66ab760732d2` | 4 new/19 legacy/build;201 QA DB pages/10001 Item ID sequence equal4 views; browser1920/768/390; CI44712653690 PASS |
| KT-119 | [55](https://github.com/cavoixanh638/kho-tri-thuc/pull/55) `codex/kt-119-related` | backend `218da95bb37d9782991915d5e67c9e77293c02fb`, UI `334a1e3363e8cdea30662fd50b3da66ca1bf763c` | 15 explicit/10 related/5 same-group separate counts;34 catalog/13 new UI/19 legacy/build; Chromium3 widths; head89c5e83 CI44738975621 pending at snapshot |
| KT-120 | [54](https://github.com/cavoixanh638/kho-tri-thuc/pull/54) `codex/kt-120-ai-review` | code `0a9cc1b962b1a9bbbf5241a821da53ddb877fb71`, final tests `493c6fd58eb57ee02b79974aa539f97b0352349d` | Provider-free PoC20 pairs;215 backend/25 new UI/19 legacy/build; conflict/undo/CSRF; CI44738350061 PASS |
| KT-121 | [53](https://github.com/cavoixanh638/kho-tri-thuc/pull/53) `codex/kt-121-templates` | `a7c1779c50e37f027019b920cf97085805edf485` | 4 templates×10 notes;46 new UI/19 legacy/14 backend/build; real pg_dump/restore15 collections; Chromium3 widths; CI44738280127 PASS |

## Bằng chứng và cách tiếp quản

KT-114: [lệnh chạy](../../../evals/readiness/README.md),
[corpus/restore](../../../evals/readiness/results.json),
[suite](../../../evals/readiness/core-suite-results.json).
KT-115/117/119 có checkpoint/evidence trên đúng nhánh PR; KT-116 có
`apps/web/tests/kt116-acceptance.md`, browser results/ảnh. KT-118 có
`KT-118-EVIDENCE.json` và ảnh cùng thư mục trên PR52. KT-120/121 có
`KT-120-EVIDENCE.md`/`KT-121-EVIDENCE.md` trên PR54/53.
Không đòi file của PR khác tồn tại ở nhánh này khi các PR chưa merge.

Mỗi task một worktree và writer; root làm114/118/120 và điều phối, các agent
làm115/116/117 rồi119/121. Mã/checkpoint đã push lên nhánh riêng. Backend dùng
QA loopback62224 với tên DB riêng; Windows8009/54329/OAuth/Drive không đổi.
Dump, credential, payload riêng không vào Git. Test frontend mới chạy tường
minh; `npm test` hiện vẫn chỉ phát hiện legacy suite.

## Phụ thuộc và các gate còn mở

- KT-114 chỉ đóng gate tổng hợp, không phải100GB/Drive quota, đổi OAuth
  host/client/project, Android hay precision ngữ nghĩa của corpus cá nhân.
- KT-116 có40 seek marks trên stream tổng hợp nhỏ với Range/auth; **private
  Drive Range, PDF thật và Android NOT_RUN**. Thiếu host capability thì báo
  NOT_SUPPORTED; thumbnail/Drive open không thành player. KT-117 Android thật
  vẫn NOT_RUN.
- KT-120 chưa có provider/budget/data permission: PROVIDER_NOT_RUN, flag mặc
  định tắt, receipt PoC stateless chưa có durable audit/revoke rejection.
  KT-120/121 là component PoC có callback contract, **chưa gắn vào main UI**.
- Root đang khép hai lỗi tích hợp bằng nhánh `codex/notes-ux-contracts`,
  **stack trên PR51**: PATCH expected_edit_version nguyên tử và renderer cho
  link nội bộ đúng UUID. Không mở tính năng khác; không merge để làm thay
  reviewer. CI/kết quả cuối nằm ở PR/checks.

Tiếp quản: đọc INDEX và checkpoint đúng PR, kiểm HEAD/CI hiện tại; không làm
lại case PASS nếu mã không đổi. Chỉ tiếp tục phần còn thiếu hoặc được giao;
giữ gate ngoài NOT_RUN, không tự bật provider, deploy hoặc merge. Root ghi
snapshot cuối trên PR48 sau CI119 và hợp đồng bổ sung.
