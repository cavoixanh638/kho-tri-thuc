# G00 — PHÂN CÔNG 17 LUỒNG CODEX SONG SONG ĐỘC LẬP (21/11/2026)

**Mục tiêu:** tối đa hóa tốc độ nhưng **không phụ thuộc kết quả của nhau**. Đã kiểm tra repo ngày 21/11/2026: KT114–121 ở PR57, KT122–126 mới có code/checkpoint trong Draft PR58/59/60/61; KT127 PR62 chỉ có service draft, KT128 chưa chạy full App, KT129 chưa thấy PR triển khai. **PR58 HEAD code SHA `91fe93950224e688471032313367bc5961385b59` CI FAIL ở frontend unit; các bước sau bị skip.** PR59/60/61 CI riêng PASS nhưng không chứng nhận merge/release. PR57 CI PASS; PR57–62 vẫn OPEN/UNMERGED.

## Khởi chạy cực ngắn

Mở **17 chat Codex/ChatGPT khác nhau**, mỗi chat một Pxx. Mọi chat đọc INDEX trên **nhánh** `coord/notes-parallel-20261121-frozen`. Prompt chung (chỉ thay mã Pxx):

`Vào GitHub cavoixanh638/kho-tri-thuc, nhánh coord/notes-parallel-20261121-frozen, đọc docs/workstreams/parallel-20261121/INDEX.md, làm đầy đủ P01, commit/push tạo PR. Không merge/deploy.`

[17 dòng prompt sao chép sẵn](LAUNCH_PROMPTS.md) | [Snapshot và giới hạn](BASELINE.md).

## Bảng phân công (tất cả có thể bắt đầu đồng thời)

| Luồng | Tác vụ | Loại | Ưu tiên | File giao riêng |
| --- | --- | --- | --- | --- |
| **P01** | Sửa CI frontend & host glue | Sửa mã | Rất cao | [P01.md](P01.md) |
| **P02** | Hoàn thiện Markdown Vault KT127 | Sửa mã | Rất cao | [P02.md](P02.md) |
| **P03** | Backup/restore schema mới | Sửa mã | Rất cao | [P03.md](P03.md) |
| **P04** | Home folder, chưa xếp nhóm, phân trang | Sửa mã | Rất cao | [P04.md](P04.md) |
| **P05** | Clipper KT126, test nguồn sạch | Sửa mã | Rất cao | [P05.md](P05.md) |
| **P06** | Citation với note do người dùng viết | Sửa mã | Rất cao | [P06.md](P06.md) |
| **P07** | HTTP Range, PDF/MP4 viewer | Sửa mã | Rất cao | [P07.md](P07.md) |
| **P08** | KT128 hành trình browser thật | Kiểm thử | Rất cao | [P08.md](P08.md) |
| **P09** | Phản biện KT122/123 hierarchy | Kiểm thử độc lập | Cao | [P09.md](P09.md) |
| **P10** | Phản biện KT124 links/outline/palette | Kiểm thử độc lập | Cao | [P10.md](P10.md) |
| **P11** | Phản biện KT125 smart collections | Kiểm thử độc lập | Cao | [P11.md](P11.md) |
| **P12** | KT129 duyệt phân loại có bằng chứng | Mô-đun độc lập | Cao | [P12.md](P12.md) |
| **P13** | Android Share/IME regression | Kiểm thử độc lập | Cao | [P13.md](P13.md) |
| **P14** | Security/IDOR/SSRF/ZIP review | Kiểm toán độc lập | Rất cao | [P14.md](P14.md) |
| **P15** | Accessibility/responsive kiểm nghiệm | Kiểm thử độc lập | Cao | [P15.md](P15.md) |
| **P16** | Đánh giá tìm kiếm tiếng Việt | Đánh giá độc lập | Trung bình | [P16.md](P16.md) |
| **P17** | Đánh giá pipeline 10k video/media | Kiểm thử độc lập | Cao | [P17.md](P17.md) |

## Cam kết độc lập và phân quyền file

1. **Một nguồn chung, không trôi:** mỗi chat tạo nhánh `codex/parallel-20261121-pxx` từ cùng **HEAD nhánh frozen** (chứa code snapshot PR58 + tài liệu P01–P17); PR vào **nhánh frozen**. Không base vào PR58/57 đang di chuyển, không lấy PR/commit Pxx khác, không merge thử vào frozen. Chỉ G00 tích hợp sau khi các PR được nộp.
2. **Một file chỉ có một chủ sửa:** P01 độc quyền `App.tsx`, `ItemScreen.tsx`, `LibraryScreen.tsx`, frontend test runner; P02 vault*, KnowledgeVaultPanel*; P03 tools/backup; P04 catalog/api/explorer; P05 processing clip*/ResearchClipper*; P06 read_knowledge/KnowledgeReading/SourceLocator; P07 storage/viewer_api; P12 OrganizationReview*; P08–P11/P13–P17 **chỉ có test/harness/evidence riêng**. Toàn bộ file chung khác **read-only**. Nếu cần kết nối, tạo contract/callback và ghi `INTEGRATION_REQUIRED`, **không sửa hộ luồng khác**.
3. **Chỉ dùng bằng chứng nguồn đóng băng:** P02 có thể *đọc* service WIP PR62 nhưng không merge hoặc cherry-pick không kiểm; các luồng QA đọc PR59/60/61 làm tư liệu nhưng kiểm **snapshot của mình**. Mọi luồng không phải chờ luồng khác; nếu journey bị thiếu Vault thì ghi `NOT_RUN/blocked`, không ngừng các test còn lại.
4. **Không tự báo PASS toàn hệ:** CI baseline PR58 đang FAIL; mỗi luồng nêu baseline status và delta; mới có test đơn vị/dữ liệu tổng hợp chỉ đạt trong phạm vi đó. Android vật lý, Google Drive thực, PDF page và media >100GB nếu chưa chạy thì ghi NOT_RUN. Không thay Drive/DB, không triển khai dịch vụ hay dùng dữ liệu/token riêng tư.
5. **Báo cáo bắt buộc:** branch, Code SHA/Tested SHA, file sửa, kiểm thử chạy và log kết quả, PASS/FAIL/NOT_RUN, diff phạm vi, giả định, khoản chưa làm, rollback, điểm cần G00 ghép. Mỗi luồng chỉ tạo `checkpoints/Pxx.md` **trên nhánh của mình**, không tự sửa INDEX/BASELINE/AGENTS/CURRENT_STATE.
6. **Không trùng việc:** P09–P11 và P14–P17 chủ yếu làm **kiểm thử/đánh giá bổ sung**, không viết lại tính năng P01–P07. P08 chạy bản frozen để phát hiện journey lỗi, không đợi P02; kết quả test có thể đỏ nhưng phải có repro khách quan.

## G00 làm SAU khi nhận PR (không phải một luồng phụ thuộc)

G00 kiểm đủ 17 PR, so sánh checklist/owner, gỡ conflict bằng adapter, ghép thử trên nhánh integration **mới**, chạy CI full/PG backup/built-App/browser, đối chiếu [38 nhóm năng lực](../notes-ux-20261120/G00-FEATURE-TRACEABILITY.md). Sau đó mới trình người dùng xét merge/deploy. **Không tự merge** PR57/58/59/60/61/62 hoặc Pxx.

**Các PR nguồn cần biết:** [PR57](https://github.com/cavoixanh638/kho-tri-thuc/pull/57), [PR58](https://github.com/cavoixanh638/kho-tri-thuc/pull/58), [PR59](https://github.com/cavoixanh638/kho-tri-thuc/pull/59), [PR60](https://github.com/cavoixanh638/kho-tri-thuc/pull/60), [PR61](https://github.com/cavoixanh638/kho-tri-thuc/pull/61), [PR62](https://github.com/cavoixanh638/kho-tri-thuc/pull/62).
