# KIỂM TOÁN VÀ ĐỐI CHIẾU KẾ HOẠCH — CHECKPOINT 22/11/2026

> **Bản ghi tiến độ, không phải giấy chứng nhận phát hành.** Căn cứ: `MASTER_PLAN.md` v4.7, `ROADMAP_AND_TESTS.md`, `CAPTURE_AND_ORGANIZE.md`, `CURRENT_STATE.md`, ma trận 38 năng lực G00 và HEAD/Actions GitHub đọc ngày 22/11/2026. Các thông số ở đây là ảnh chụp tại thời điểm kiểm tra, **không tự cập nhật** nếu không chạy lại kiểm toán.

## 1. Kế hoạch gốc vẫn là chuẩn

- **A (P0):** tiếp nhận nguyên văn/giờ server, tải và xác minh Google Drive, thumbnail, backup/restore, idempotency/recovery.
- **B (P0):** nguồn web/video, text/phụ đề, tự xếp nhóm có sẵn, RelatedItem, tìm kiếm tiếng Việt và **đo độ chính xác**.
- **C (P1):** pilot ChatGPT Google Drive app + bản xuất tri thức; MCP chỉ khi pilot không đủ.
- **D (theo yêu cầu):** OCR/ASR, AI nâng cao, Android native, storage thứ hai, semantic search.
- **Thay đổi phạm vi đã được người dùng yêu cầu sau baseline:** ô nhập thống nhất cho link/tệp/ảnh/text và OCR ảnh bằng Gemini có cơ chế khám phá/chọn model, consent theo tài khoản. Đây là phần D được **cho phép phát triển**, không thay thế cổng A/B. Android chủ động hoãn; không tự biến thành blocker phát hành web/Windows giai đoạn đầu.

## 2. Tình trạng GitHub thực tế tại checkpoint

| Thành phần | Vị trí (22/11/2026) | Chứng cứ | Trạng thái đúng |
| --- | --- | --- | --- |
| Bản `main` | `1f64f50147b9f92177b3e04f787a36fc673736d6` | GitHub branch main | Bản chuẩn lịch sử; không có các PR mới |
| PR #79 | `2c3410bbc5978f4ce0c0af1b2efe392e099a16e6` → nhánh frozen | CI #44902095620 SUCCESS | Code candidate, **OPEN/DRAFT/UNMERGED** |
| PR #81 | `27920611912ce4412a6a45022f1bfa82e5a1d09c` → nhánh integrated | CI #44908925201 SUCCESS | Unified Inbox candidate, **OPEN/DRAFT/UNMERGED** |
| PR #82 | `b3049ab031f048a546f29258fdf37ee3f75a6bbc` → #81 | CI #44921582154 SUCCESS | Gemini model selector, **OPEN/DRAFT/UNMERGED** |
| PR #84 | `7c3832a0137341fc54435b6055c007ef4df347f8` → #82 | CI #44971811417 SUCCESS | Gemini OCR **mock-tested**, OPEN/DRAFT/UNMERGED; không có API inference thực |
| So sánh với main | Candidate PR84 **ahead 232 / behind 26**, tình trạng `diverged` | GitHub compare main...PR84 | **Chưa thể coi release-ready** dù từng PR có `mergeable=true` theo target cũ |

**57 PR đang mở** tại thời điểm chụp, gồm nghiên cứu, test độc lập, nhánh nguồn và PR tích hợp; **không phải 57 feature thiếu**. Không tự merge chồng toàn bộ. Trước mỗi lần tích hợp lấy lại HEAD/PR state/compare từ GitHub; số liệu có thể đã thay đổi.

## 3. Truy vết P0/P1 theo yêu cầu và chứng cứ (không tự thăng PASS)

| Nhu cầu/ID gốc | Code/bằng chứng đã thấy | Bước còn thiếu để nghiệm thu | Mức | Trạng thái |
| --- | --- | --- | --- | --- |
| A / KT001–011 / N01–05,13–15 | Django/PostgreSQL, CaptureEvent/DriveStorage/Job, pilot backup và restore Windows/Drive | E2E trên bản ứng viên sau tích hợp; full readback file thật, backup/restore nhiều nhóm/note/relations, worker kill/restart | P0 | **PARTIAL_VERIFIED** |
| A / tiếp nhận chung bổ sung | PR81 + frontend/Pg/Chromium QA | Lượt gửi nhiều file thật, retry, quyền, không mất caption, Drive verified đối với bản ứng viên | P0 | **CANDIDATE_CI_PASS** |
| B / KT101; media 10k | FB video download 128 MiB; link/metadata YouTube/TikTok; P17 fixtures | Tải/đọc lại có phép trên từng nền tảng, video lớn, quota/timeout, thử 100→1k→10k; `>=100GB` khi có môi trường/ngân sách | P0 | **PARTIAL / SCALE_NOT_RUN** |
| B / KT102; KT108/112 | Parser PDF/DOCX/XLSX, pypdf/PDFium benchmark có giới hạn, ASR local faster-whisper 600s | PDF tiếng Việt đa nguồn/bảng/scan; thực tế MP4 time seek/audio; ASR dài hơn nếu yêu cầu | P0 | **PARTIAL** |
| B / KT103/107/110; KT129 | OrganizationService + RelatedItem + review UI candidate | Bộ 30–50 mục tiếng Việt được con người gắn gold, precision, coverage, sai nhóm và related-recall | P0 | **QUALITY_NOT_RUN** |
| B / KT104; P16 | Hai GIN FTS, P16 28 Item/86 gold queries | Chạy 86 câu thật với PostgreSQL và ghi Recall@5/Precision@5/P95, quyền giữa owners, 10k DB | P0 | **BENCHMARK_NOT_RUN** |
| B / KT122–128, P08/P15 | Candidate explorer/notes/wiki/vault; P08 Chromium 9/13 PASS | J3 public opt-in; J6B verified PDF/MP4; J8 vault roundtrip; J9 10k/restore; P15 keyboard/focus | P0 | **RELEASE_UAT_NOT_RUN/FAIL** |
| C / KT201–202E | Pilot 8 Item/9 câu hỏi, full readback có version; query đầu đúng 8/9, fallback tìm 9/9 | Trải nghiệm trực tiếp ChatGPT độc lập, corpus đại diện, quyết định MCP theo bằng chứng | P1 | **CONTROLLED_PILOT_PASS_WITH_LIMITS** |
| D / Gemini bổ sung | PR82, PR84 model discovery/consent/adapter, 394 backend tests được báo trong CI | API key thử nghiệm do người dùng cho phép, bộ ảnh tiếng Việt có gold, quota/giá và chính sách dữ liệu, duyệt model | P1 | **MOCK_PASS / LIVE_NOT_RUN** |
| D / Android | PWA share có source-contract, một phần browser synthetic | Thiết bị Android thật sau khi người dùng khởi động lại hạng mục này | DEFER | **DEFERRED_BY_USER** |
| D / B2/R2, vector, chatbot riêng | Không phải P0 | Chỉ mở lại khi có trigger đo được hoặc lệnh người dùng | DEFER | **NOT_PLANNED_NOW** |

**Chú ý công thức:** P08 trên run #44971811417 = 9 PASS, 0 FAIL, 0 BLOCKED, 4 NOT_RUN (13 ca), `PASS/(PASS+FAIL)=9/9=100%` *trong số đã chạy*, còn `completion=9/13`, **không được gọi UAT PASS**. Các ca NOT_RUN **không nằm trong mẫu số executed**, lý do nêu ngay ở row (J3/J6B/J8/J9). Các tỷ lệ đánh giá chất lượng chưa chạy thực có mẫu số 0 phải ghi `NOT_RUN`, không quy thành 0% hay 100%.

## 4. Lỗi nghiệm thu đã phát hiện (phải khắc phục)

1. **CI xanh nhưng P08 chưa hoàn chỉnh**: workflow #44971811417 có hai bước `continue-on-error: true`; script `knowledge_journeys.mjs` trả exit=2 do `NOT_RUN`. Job `browser_acceptance` vẫn SUCCESS.
2. **P15 không qua kiểm focus**: `AssertionError: Cannot focus .research-clipper select`. Component clipper đã đưa vào vùng `<details>` đóng mặc định; kiểm thử cần thao tác mở bằng bàn phím rồi mới kiểm select. Không được tắt test để che lỗi.
3. **P08 J8** có `NOT_RUN` mã hóa cố định về bản frozen thiếu KT127, dù bản candidate đã thêm Vault; phải thay bằng E2E thực sau tích hợp, không suy từ API tồn tại.
4. **P16/P17 chưa là E2E/benchmark**; hiện workflow `smoke.yml` không gọi `p16_eval.py`/`p17_media_eval.py`. Test khác PASS không đồng nghĩa hai task PASS.
5. **Kế hoạch/hiện trạng trên main chưa cập nhật nhánh mới**; cần ghi rõ code SHA/tested SHA/GitHub URL và giữ lịch sử QA không bị ghi đè.

## 5. Thứ tự thực hiện rút gọn (không thêm overengineering)

| Thứ tự | Task chịu trách nhiệm | Đầu ra có thể kiểm | Điều kiện chuyển bước |
| --- | --- | --- | --- |
| P0-01 | G00 / KT114 / PR79,81,82,84 | Nhánh release-candidate từ `main` mới nhất, ma trận diff và mỗi thay đổi có chủ sở hữu, reconcile 26 commits `behind`; backup migration | Mọi API/migration/test đã xét, **không merge/deploy** cho tới khi người dùng duyệt |
| P0-02 | P08/P15/KT128 | Sửa clipper focus; browser gate không biến incomplete thành SUCCESS; danh sách J3/J6B/J8/J9 có hướng chạy thực và kết quả | Có screenshot, số ca và nguyên nhân FAIL/NOT_RUN; release gate tách CI build |
| P0-03 | KT101/102/103/104/107/110, P16/P17 | Demo lưu→đọc→xếp nhóm→tìm→phát nguồn; 30–50 gold VN, 86 queries trên DB và 10k scale đã định nghĩa | Có số liệu thật với tử/mẫu số, giấy phép/điều kiện nguồn |
| P1-01 | KT201/202E + Gemini PR82/84 | Pilot ChatGPT UI và Gemini ảnh được phép với cost cap, ghi `modelVersion` | Chỉ chạy API/provider thật sau quyền và ngân sách |
| P1-02 | KT114 / ops | Thử deployment an toàn, HTTPS, restore và rollback với dữ liệu kiểm soát | Người dùng xét merge/deploy |
| DEFER | Android native, B2/R2, semantic/chatbot | Không tạo blocker mới | Chỉ mở theo chỉ đạo |

## 6. Quy tắc đối chiếu **trước và sau MỖI PR / checkpoint**

1. **Trước khi sửa:** đọc `MASTER_PLAN` → `ROADMAP_AND_TESTS` → `CURRENT_STATE` → ma trận này, kiểm tra HEAD PR/base/main mới nhất, chọn đúng ID KT/Pxx và cổng A–D. Nếu task mới, cập nhật *phạm vi và tiêu chí* trước, không cho phép ghi dấu PASS trước khi test.
2. **Trong khi sửa:** không đổi yêu cầu gốc để hợp thức hóa code; giữ định danh, quyền, provenance và rollback. Chỉ CI/unit/mock mà chưa có live thì ghi `MOCK_PASS`, không suy chất lượng thực.
3. **Trước PR:** tự kiểm diff trong phạm vi; cung cấp Code SHA, Tested SHA, môi trường, bộ dữ liệu, lệnh test, PASS/FAIL/NOT_RUN và lý do; **đính kèm phần “Đối chiếu kế hoạch”** trong mô tả PR.
4. **Sau khi CI:** đọc **bên trong từng step** và báo cáo artefact P08/P15/P16/P17, không nhìn duy nhất workflow xanh; phân biệt compile/unit/browser/synthetic/provider thật; ghi công thức nếu có số liệu.
5. **Sau review/tích hợp:** chỉ G00 cập nhật `CURRENT_STATE.md` (tránh nhiều agent sửa đồng thời); giữ `MASTER_PLAN` là phạm vi, `ROADMAP_AND_TESTS` là tiêu chí, `CURRENT_STATE` là tiến độ, bảng này là ảnh chụp đối chiếu/điều phối. Khi không làm thêm, **không có tiến trình tự chạy nền** chỉ vì tài liệu ghi “liên tục”.
6. **Định kỳ khi phát triển:** trước mỗi gói công việc mới phải rà lại status/plan, backlog và cổng còn thiếu. Không tạo cron GitHub Actions full Docker mỗi ngày; tránh chi phí CI vô ích. Chỉ đề nghị lịch kiểm tra tự động riêng khi có chủ trương.

## 7. Chốt trạng thái / rollback

- Nhánh tài liệu này là **đề nghị đưa quy tắc đối chiếu vào main**, không có code production, không sửa dữ liệu. Trạng thái của PR sản phẩm #79/#81/#82/#84 giữ nguyên.
- Nếu phải rollback, đóng PR/revert riêng các file quy định; không có migration, Drive/OAuth/AI gọi trả phí.
- **Không kết luận “đã xong dự án”** khi các gate P0 còn `NOT_RUN/FAIL`; sau mỗi lần cập nhật phải ghi rõ `NEXT` theo thứ tự trong bảng mục 5.
