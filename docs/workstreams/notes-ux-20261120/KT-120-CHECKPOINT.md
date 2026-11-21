# KT-120 — review đề xuất không bật provider

Branch `codex/kt-120-ai-review`, baseline7044b4a. User đã giao task; chưa cấp
provider/budget/data permission nên chỉ triển khai PoC nhận đề xuất do người
dùng cung cấp, provider/model none. Không gọi model/trả phí/OAuth/Drive.

Đã viết API preview/accept/reject/undo với signed receipt15phút chứa owner/item,
source fingerprint, base_edit_version và before/after. Preview/reject không ghi;
accept/undo lock Item, kiểm note/version/source rồi tăng version +organize job.
Không migration/bảng suggestion. Router feature gate mặc định404; PoC chỉ bật
bằng override_settings trong test, chưa nối vào ItemScreen đang thuộcKT115.

UI riêng AiSuggestionReview/Diff hiển thị before/after/chênh lệch Unicode, accept/
reject/cancel/undo explicit, chặn draft khác và lỗi409 không overwrite. Không
thay Markdown renderer và không renderHTMLnguồn.

Code đã push `0a9cc1b962b1a9bbbf5241a821da53ddb877fb71`; 20fixtureVietnamese
preview/reject/accept/undo bảo toànItem/Event/Asset/pinned PASS. Backend215test
PASS/0skip, newfrontend25PASS, legacy19PASS, build/Ruff/diff PASS. Test mới thêm
late receipt và409/503; payload/semantics không đổi. BrowserNOT_RUN: IAB không
khả dụng, nativeChrome minimized không lấy được binding; không dùng DOM làm
browserPASS. [Bằng chứng](KT-120-EVIDENCE.md).

Receipt stateless chỉ làPoC, không có durableaudit/revokereject; UI loại receipt,
server vẫn chốngexpiry/version/replay. Không gọi là AIđãtíchhợp. Tiếp commit
evidence/push/PR, theoCI; khôngmerge. Cần tíchhợp callbackAPIvàItemScreen sau khi
cácPRđược review; provider thật PROVIDER_NOT_RUN.
