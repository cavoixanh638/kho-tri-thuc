# G00 — Kiểm tra hoàn tất 17 luồng và chốt việc cần giao tiếp (21/11/2026, 12:05 ICT)

**Trạng thái:** kiểm toán GitHub PR/branch/checkpoint/CI; **không merge, không deploy, không sửa production**.  
**Nguồn gốc:** [frozen INDEX](INDEX.md), PR #57–#75; bản snapshot mã **`91fe93950224e688471032313367bc5961385b59`**, base frozen `9716a6a876d6ec41e10b3c3dcbdc095ab4ddd84d`. G00 dùng nhánh kiểm toán riêng `coord/notes-parallel-20261121-g00-review` để không thay nhánh gốc frozen.

## 1. Kết quả đối chiếu

- **13/17 luồng có PR:** P01–P07, P09–P12, P16–P17 = PR #63–#75; tất cả PR đều vào đúng `coord/notes-parallel-20261121-frozen`, chưa merge.
- **4/17 luồng chưa có thay đổi trên GitHub:** P08, P13, P14, P15 **có branch** `codex/parallel-20261121-pXX` nhưng **HEAD giống hệt frozen** (0 commit ahead, 0 file changed). Không có PR/checkpoint mới của bốn luồng này. **Không dùng thông báo chat “xong” làm bằng chứng hoàn thành.**
- **P01 PR #67**: GitHub Actions **SUCCESS tại HEAD `92117c433a615e93d20793a00a685491f8a1e7a5`**, [run 44862119636](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44862119636); checkpoint ghi 289/289 frontend PASS trong run trước và full synthetic CI PASS. P01 dùng error boundary/fallback; cần kiểm contract `/items/:id/structure` thực sự, không che lỗi dữ liệu.
- **12 PR khác CI đỏ tại HEAD**: mọi workflow thất bại ở bước `Test all frontend DOM and unit suites` và **đều skip backend, migration, backup, smoke**. Vì các branch Pxx xuất phát từ frozen CI đỏ **trước** P01, không suy đây là 12 lỗi chức năng độc lập; nhưng cũng **không được tuyên bố PASS** khi chưa chạy lại trên nhánh tích hợp có P01.
- P02/P03/P06/P12 Draft; các PR QA chỉ có test/báo cáo; P02 vault và P12 review **chưa được mount vào router/host**, P06 citation bridge chưa mount. Dữ liệu Drive thật, MP4/PDF seek, Android vật lý, UAT UI thật, PostgreSQL restore v4, benchmark media thật đều NOT_RUN nếu thiếu evidence.

| Luồng | PR | CI tại HEAD | Tình trạng không thể suy thành nghiệm thu |
| --- | --- | --- | --- |
| P01 | [#67](https://github.com/cavoixanh638/kho-tri-thuc/pull/67) | PASS | Fix error-boundary / structure; full CI green at 92117c4 |
| P02 | [#69](https://github.com/cavoixanh638/kho-tri-thuc/pull/69) | FAIL (frontend gate) | Vault ZIP candidate; backend+DOM+roundtrip not executed |
| P03 | [#63](https://github.com/cavoixanh638/kho-tri-thuc/pull/63) | FAIL (frontend gate) | Backup manifest v4; PostgreSQL 18 restore not executed |
| P04 | [#64](https://github.com/cavoixanh638/kho-tri-thuc/pull/64) | FAIL (frontend gate) | Unfiled/home folder and mixed paging; PG tests not executed |
| P05 | [#68](https://github.com/cavoixanh638/kho-tri-thuc/pull/68) | FAIL (frontend gate) | Clip source identity/retry; full E2E not executed |
| P06 | [#71](https://github.com/cavoixanh638/kho-tri-thuc/pull/71) | FAIL (frontend gate) | Authored note citation bridge; host mounting still required |
| P07 | [#65](https://github.com/cavoixanh638/kho-tri-thuc/pull/65) | FAIL (frontend gate) | HTTP Range suffix correction; real Drive/page navigation NOT_RUN |
| P08 | — | NO NEW COMMITS | Only branch at frozen HEAD; no E2E evidence/PR |
| P09 | [#70](https://github.com/cavoixanh638/kho-tri-thuc/pull/70) | FAIL (frontend gate) | Audit: unfiled mismatch; children cap 50; backup projection |
| P10 | [#73](https://github.com/cavoixanh638/kho-tri-thuc/pull/73) | FAIL (frontend gate) | Audit: 2 parser + 2 wiki autocomplete confirmed helper fails |
| P11 | [#66](https://github.com/cavoixanh638/kho-tri-thuc/pull/66) | FAIL (frontend gate) | Audit: Timeline ordering/caption; invalid legacy query risk |
| P12 | [#72](https://github.com/cavoixanh638/kho-tri-thuc/pull/72) | FAIL (frontend gate) | Rule-based review candidate; router/UI mounting not done |
| P13 | — | NO NEW COMMITS | Only branch at frozen HEAD; Android/IME harness missing |
| P14 | — | NO NEW COMMITS | Only branch at frozen HEAD; security audit missing |
| P15 | — | NO NEW COMMITS | Only branch at frozen HEAD; accessibility evidence missing |
| P16 | [#74](https://github.com/cavoixanh638/kho-tri-thuc/pull/74) | FAIL (frontend gate) | 86 gold queries prepared; actual PG search NOT_RUN |
| P17 | [#75](https://github.com/cavoixanh638/kho-tri-thuc/pull/75) | FAIL (frontend gate) | 50 synthetic URLs/media fault cases; real Drive/media NOT_RUN |

## 2. Các lỗi do luồng QA tìm thấy, phải vào gate tích hợp

1. **P09:** `explorer.children` và `catalog.api.list_items` sai lệch “chưa xếp thư mục” với shortcut; `structure_info` giới hạn 50 child nhưng UI thiếu phân trang; portable backup chưa đủ home/parent/order/version. P04 và P03 có patch liên quan **nhưng chưa chạy DB thật**, không tự đánh dấu đã sửa.
2. **P10:** Parser Markdown bỏ lọt link sát dấu câu và nhiều link liền nhau; wiki autocomplete sai khi sau inline code đóng hoặc trong fence không đóng đúng. Audit helper 14 PASS/2 FAIL và 10 PASS/2 FAIL; cần patch độc lập `groups_api.py` và `WikiCompletion.ts` + browser/IME regression.
3. **P11:** Timeline đổi thứ tự `published_desc/title` khi nhóm theo ngày nhận; caption không phản ánh sort; JSON query cũ không hợp lệ có nguy cơ HTTP500 (chưa runtime confirm); cần test và fix ở `LibraryViews.tsx`/`collection_api.py`; benchmark PG 10k chưa chạy.
4. **P17:** Chính sách `verified media` cần **byte stream + SHA + Drive full readback**; metadata-only/URL không chứng minh lưu video. Các vấn đề đầu vào `result.json`, 429/403, giới hạn nguồn 128MiB và download không resume cần tái hiện trước khi sửa worker hoặc tăng giới hạn.
5. **P01:** CI xanh nhưng error boundary có thể chỉ hiện fallback khi structure API trả thiếu field, cần test API thật với 1 bài có con và một bài có note gốc; không báo folder tree trọn vẹn chỉ vì suite pass.

## 3. Việc cần giao, không mở lại tất cả 17 luồng

### A — Yêu cầu bốn luồng cũ hoàn tất giao nộp (làm song song)

**P08/P13/P14/P15:** quay lại chat/luồng cũ, thực hiện đúng `P08.md`/`P13.md`/`P14.md`/`P15.md` ở frozen, commit/push trên branch cá nhân đang có và mở PR **base frozen**. Không được chỉ reply “đã xong” nếu không có SHA/PR/checkpoint. Nếu không thể chạy hardware/real browser, vẫn phải commit **test harness + report NOT_RUN**.

### B — Một luồng G00 tích hợp ngay với các PR đã có, không chờ bốn luồng A để bắt đầu

- Tạo branch **mới** từ `coord/notes-parallel-20261121-frozen`, không trực tiếp sửa frozen/main/PR #57/#58.
- Tích hợp có kiểm soát patch **P01 trước** để CI baseline xanh. Sau đó đưa P02–P07, P12 vào candidate; các PR P09/P10/P11/P16/P17 là tests/audits, không tạo code feature trùng.
- P01 owning `ItemScreen.tsx` phải mount sau review `SourceCitationBridge` (P06), `OrganizationReview` (P12), `KnowledgeVaultPanel` (P02); `config/api.py` chỉ do G00 nối router. No AI provider default OFF, preserve authored note.
- Chạy toàn bộ frontend/backend/migrations tests, PostgreSQL 18 temp backup v1–v4, media Range, browser app journeys, scope, security; ghi *exact* Code SHA/Tested SHA, PASS/FAIL/NOT_RUN, blockers. Xử lý cấu trúc API, parser/link, sort/filter và quyền access trước khi báo ready.
- Báo riêng thiếu quyền test Android thật / Drive thật / 100GiB media và hướng dẫn UAT, không tự gọi PASS.
- Tạo PR **target frozen**, **không merge/deploy**; không áp lại PR #57–#62 vốn đã nằm trong frozen snapshot.

### C — Hai patch độc lập nếu muốn rút ngắn thời gian (có thể làm ngay, song song với A+B)

- **FIX-NAV:** một AI chỉ sửa Markdown internal-link parser + wiki trigger, dựa 4 lỗi P10, sở hữu `apps/backend/catalog/groups_api.py`, `apps/web/src/WikiCompletion.ts`, tests tên `fix_nav_*.py` / `fix-nav*.test.mjs`. Branch riêng từ frozen, PR target frozen. Không sửa App/ItemScreen/LibraryViews.
- **FIX-COLLECTIONS:** một AI chỉ sửa Timeline order/caption và validate persisted query theo P11, sở hữu `apps/web/src/LibraryViews.tsx`, `apps/backend/catalog/collection_api.py`, test riêng. Branch từ frozen, PR target frozen. Không sửa App/ItemScreen/vault/backup.

### D — Chưa nên cấp phép merge/release

**Blockers:** P08 E2E, P14 security, P03/02 PostgreSQL restore/import, CI tổng hợp, P13 mobile/IME, P15 accessibility. Các giới hạn thiết bị hoặc tài khoản thực phải thành NOT_RUN với lý do, không “0 lỗi”. Người dùng quyết định chấp nhận rủi ro sau khi xem đầy đủ kết quả.

## 4. Prompt ngắn

- **Bốn luồng cũ:** `Vào GitHub cavoixanh638/kho-tri-thuc, nhánh coord/notes-parallel-20261121-frozen, hoàn tất P08 [đổi mã], commit/push checkpoint và tạo PR vào nhánh frozen. Không merge/deploy.`
- **G00:** `Vào GitHub cavoixanh638/kho-tri-thuc, đọc docs/workstreams/parallel-20261121/G00-NEXT-GATES.md trên nhánh coord/notes-parallel-20261121-g00-review, chủ trì tích hợp các PR Pxx trên nhánh riêng, sửa gate lỗi và chạy full CI, tạo PR về frozen; không merge/deploy.`

**Không tạo thêm 20 luồng mới:** trước hết hoàn tất bốn luồng trống, patch hai nhóm lỗi độc lập, G00 tích hợp và QA. Bằng chứng pass phải đúng commit cuối, không vì PR được mở mà coi feature chạy được.
