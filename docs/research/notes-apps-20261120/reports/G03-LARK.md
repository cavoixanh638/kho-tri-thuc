# G03 — Nghiên cứu độc lập Lark Docs / Wiki / Base (20/11/2026)

**Phạm vi:** Lark quốc tế (larksuite.com), gồm Docs, Wiki, Base và Minutes như phần bổ trợ; không nghiên cứu báo cáo của luồng khác.  
**Thời điểm chốt và truy cập nguồn:** 20/11/2026, múi giờ Asia/Ho_Chi_Minh.  
**Đối chứng nội bộ:** cavoixanh638/kho-tri-thuc, nhánh main tại SHA **c97f5678a6893d7dfec2595d89c9122f05195320**.  
**Phương pháp:** xem tài liệu sản phẩm, help center, release notes, developer API, GitHub dự án chính thức; đọc mã nguồn hiện có của Kho Tri Thức. **Không đăng nhập tài khoản Lark, không nhập dữ liệu người dùng, không cài CLI/SDK/MCP, không benchmark live.** Toàn bộ kịch bản thao tác thực tế Lark: **NOT_RUN**; các trạng thái NATIVE/EXTENSION bên dưới là đánh giá năng lực từ tài liệu, không phải kết quả test.  
**Quy ước bằng chứng:** [Sxx] nguồn ngoài; [Cxx] đường dẫn mã/dữ liệu Kho Tri Thức cuối bài. Marketing/Help Center chỉ chứng minh nhà cung cấp công bố tính năng; không chứng minh độ chính xác tiếng Việt hay tương thích tích hợp.

## 1. Executive summary (dưới 200 từ)

**Kết luận: Tham khảo UX và chọn PoC hẹp; không thay toàn bộ Kho Tri Thức bằng Lark.** Lark Docs/Wiki/Base có năng lực mạnh về soạn thảo cộng tác, cây tài liệu, liên kết hai chiều, nhiều chế độ xem và tự động hóa. Từ bản cập nhật Lark năm 2026, Base hỗ trợ dán chữ/ảnh để AI đưa vào trường, Categorization/Smart Tags, và workflow [S01–S06]. Minutes cho phép bấm transcript để tìm đúng thời điểm ghi [S10].

Tuy nhiên, **AI field autofill không đồng nghĩa tự nhận URL video, trích nội dung thực, bảo toàn từng lượt nhận và tự gán các nhóm đang có theo bằng chứng**. Những thuộc tính này là phần mềm và dữ liệu thật của Kho Tri Thức [C01–C07]. Lark hiện giới hạn 2.000 hàng/bảng ở Starter, 20.000 ở Pro, có quota tự động hóa và khác biệt xuất dữ liệu [S12–S15]. Export Base không gồm lịch sử chỉnh sửa và bình luận [S14]. Việc đổi sang Lark cũng khiến kho file Google Drive, PostgreSQL, định danh và lịch sử phụ thuộc di trú khó kiểm chứng. Giá trị học hỏi cao nhất là **AI-assisted structured intake**, **view đa dạng**, **backlinks dễ hiểu** và **gắn transcript vào playback**.

## 2. Bằng chứng sản phẩm — phân biệt công bố và thử nghiệm

| Nội dung | Trạng thái từ nguồn | Đánh giá có điều kiện |
| --- | --- | --- |
| **AI import chữ/ảnh** vào các trường Base | **Đã công bố/phát hành**; bản V7.67 công bố 07/05/2026: dán text/ảnh, AI nhận diện và điền trường [S01, S02] | Là AI mapping **trong Base**, chưa có chứng cứ tự tải và hiểu toàn video qua link Facebook/TikTok/YouTube |
| **Categorization, Smart Tags, Smart Extraction, Summary, Custom AI Autofill** | **Đã công bố**, có rule, tham chiếu option trường khác, auto-update; có lựa chọn AI nội bộ hoặc mô hình bên ngoài [S03] | Tham chiếu category/tag có sẵn là tín hiệu hữu ích. Smart Tags/Categorization sinh **giá trị field**; không phải bằng chứng tạo ItemTopic/ItemProject/ItemTag an toàn như Kho Tri Thức. **Cảnh báo từ tài liệu:** tạo shortcut trên trường có dữ liệu có thể ghi đè nội dung không khôi phục; nên tạo trường mới |
| **Workflow và automation** | **Đã công bố**, có trigger khi bản ghi tạo/sửa, hành động cập nhật/tạo; workflow có If/Else, Switch, Loop, nhưng hành động **Update record with AI không được workflow hỗ trợ** theo bảng so sánh [S04, S05] | Phải kiểm tra trigger đầu vào, điều kiện và hành động; đừng mặc định một chuỗi AI tự phân loại sẽ hoạt động trong mọi loại workflow |
| **AI-recommended linked records** | Tài liệu giới thiệu Lark đề cập gợi ý liên kết các record liên quan; AI trường/gợi ý không phải bảo chứng tự ghi một quan hệ có provenance [S01, S06] | Cần kiểm thử rõ *suggestion vs saved link*, xử lý sai và sự ưu tiên liên kết do người dùng tạo |
| **Wiki/Docs, backlinks** | Wiki hỗ trợ cây trang, tạo/di chuyển/shortcut, quyền theo tổ chức–không gian–trang; Docs hỗ trợ Markdown shortcuts, bảng, video, file; @document tạo liên kết hai chiều/backlink [S07–S09] | Wiki là mục lục thiên về tài liệu cộng tác, không mặc định quan hệ many-to-many của một Item tri thức tùy ý trong nhiều Topic |
| **Minutes** | Đã có transcript tương tác: bấm chữ chuyển playback đúng vị trí; desktop có nhập audio/video; mobile có ghi; file upload tối đa **4 GB**, bản ghi tối đa **16 giờ** [S10, S11] | Tính năng transcript **không có ở Starter/Basic** [S11]; chưa đo tiếng Việt, độ lệch thời gian, cũng không thay cho nguồn URL video internet |
| **Ứng dụng Windows/Android; offline** | Có client Windows và Android; Docs cho phép bật sửa offline **trên mobile** rồi sync khi online [S16, S17]; Docs edit history có giải thích bản ghi local khi mất mạng [S18] | Chưa chứng minh offline cho mọi Base, Wiki, file video, Windows; xung đột khi cùng sửa chưa chạy test |
| **Export và portable backup** | Docs tải Markdown/Word/PDF từ desktop, mobile Word/PDF/PNG; Base xuất .base/.xlsx/.csv từ web/desktop [S13, S14]. .base là định dạng riêng của Lark; **không xuất comment, basic permission, edit history, template ID** | Các biểu hiện export không chứng minh backup có thể khôi phục đầy đủ lịch sử/định danh/asset. API Drive export v1 tài liệu hóa docx/pdf cho docx, khác với tùy chọn Markdown từ UI [S19] |
| **API/SDK/MCP** | Open Platform có Docs block APIs và Base record/table APIs; repo SDK Python MIT, MCP OpenAPI chính thức **beta**, CLI chính thức có Docs/Base/Wiki [S20–S23] | Tích hợp phải tạo app, cấp scope/OAuth; MCP beta nói rõ **chưa hỗ trợ upload/download** và **không chỉnh trực tiếp cloud docs**, không đánh đồng với tất cả API/CLI. Không cài hoặc sử dụng trong lượt này |
| **Giá và quy mô** | Starter $0, Basic $6, Pro $12/người/tháng (bảng năm, giá trang chính thức), Enterprise liên hệ; Base 2.000 / 2.000 / 20.000 / 50.000 hàng mỗi bảng; automation 1.000 / 1.000 / 50.000 / 500.000 runs/tháng [S12, S15] | >10.000 Item **vượt Starter một bảng**; chia bảng hoặc Pro làm tăng chi phí/độ phức tạp; lưu hàng trăm GB video phải rà storage và upload cap theo gói, không coi là khả năng có sẵn từ Drive |
| **Privacy/license** | Chính sách Lark ghi workplace information không dùng train/fine-tune AI **trừ khi Workplace Owner cho phép**; AI service có quyền xử lý dữ liệu được phép truy cập; vị trí lưu dữ liệu quyết định khi tạo tổ chức [S24–S26] | Lark Docs/Base/Wiki là SaaS đóng; **MIT của SDK/MCP không phải giấy phép tự host sản phẩm**. Trước tích hợp phải kiểm soát vùng dữ liệu, quyền app, bên thứ ba nhận prompt, điều khoản và chi phí thực tế |

**Lưu ý độ mới:** Help Center có bài 2025/2026; [S02] là release note ghi ngày phát hành 07/05/2026. Các giới hạn AI trên help center có thể là **ưu đãi/tạm miễn phí**, không biến thành bảo đảm lâu dài: [S27] ghi quota AI tích hợp chỉ miễn phí tạm thời. Không tuyên bố một tính năng được thử vận hành chỉ vì đã có release note.

### Ba chỗ dễ hiểu nhầm cần phản biện

1. **AI Import ≠ CaptureEvent.** Dán ảnh/chữ rồi map cột là hành động UI; chưa có bằng chứng tiếp nhận URL, lưu server timestamp bất biến, nhận diện duplicate nhưng giữ lượt gửi khác retry, nguồn xuất bản và nguồn trích.
2. **Smart Tags/AI liên kết ≠ tự tổ chức có kiểm chứng.** Lark có giá trị AI cho trường và gợi ý bản ghi liên quan; Kho Tri Thức phải phân biệt nhóm có sẵn, nhóm do người dùng ghim, phiên bản thuật toán, xác suất/chứng cứ và không ghi đè người dùng [C03, C04]. Hành vi tương đương cần đo **ghi quan hệ thực** sau khi nội dung trích đáng tin, không phải chỉ thấy một ô tag.
3. **Minutes ≠ hiểu mọi video.** Bấm transcript là UX tốt **khi có transcript đồng bộ**; không suy ra AI đọc được video Facebook/TikTok chỉ từ title, lượt xem, thumbnail, hay URL. Với video chưa có transcript, hiển thị đúng trạng thái thiếu text như Kho Tri Thức [C05].

## 3. K01–K12 — ma trận có đường tái thử

**Cách đọc trạng thái:** đánh giá **toàn bộ tình huống** cần cho Kho Tri Thức, không chỉ một khả năng phụ. NATIVE = có chức năng tương ứng từ sản phẩm; EXTENSION = cần nối/kết hợp trong Lark; CUSTOM_BACKEND = vẫn cần backend nghiệp vụ riêng; UNVERIFIED = chưa đủ nguồn xác nhận toàn ca; NOT_SUPPORTED = có nguồn nói không hỗ trợ. Bất kỳ ca nào cũng **LIVE NOT_RUN** vì không có Lark workspace được phép dùng. Link Sxx ở cuối là nguồn để tái thử.

| Ca | Trạng thái toàn ca | Bằng chứng/cụ thể đã có | Bước tái thử tối thiểu và điều chưa chắc |
| --- | --- | --- | --- |
| **K01** — ghi chú Việt, receipt và giờ | **CUSTOM_BACKEND** | Docs soạn văn bản có autosave; Base có Created at [S08, S28]. Không có nguồn đảm bảo receipt server timestamp **bất biến theo mỗi lần nhập** | Tạo note "Công nghệ – Hải Phòng", kiểm dấu NFC; ghi thời điểm ở UI, sau sửa/lưu lại xem dữ liệu API. So với CaptureEvent là **chưa chứng minh** |
| **K02** — URL video/web tự lấy metadata+content | **CUSTOM_BACKEND** | Base có hyperlink, Docs có chèn link/video; AI import là text/ảnh dán [S01, S28], **không phải crawler** | Dán URL YouTube, TikTok, Facebook và URL web HTML; kiểm có thực lấy title, source ID, transcript hay chỉ link/preview; đối chiếu dữ liệu. **NOT_RUN** |
| **K03** — URL trùng sau 1 ngày vs retry | **CUSTOM_BACKEND** | Base Created at/updated; API create record [S20, S28]. Không có cam kết cặp Event/Item/idempotency | Gửi URL lần 1, gửi lại sau 24h, retry cùng request key; đo 2 events/1 item và 1 event/1 retry, nếu không thì cần code riêng [C01] |
| **K04** — Markdown/bảng/link/Unicode roundtrip | **NATIVE** (một phần) | Docs hỗ trợ bảng, Markdown shortcuts, tải Markdown/Word/PDF trên desktop [S08, S13] | Soạn bảng 3 cột, links, tiếng Việt NFC, tải Markdown rồi nhập lại, diff nội dung và asset. Roundtrip lossless và version history export **chưa xác thực** |
| **K05** — nhận diện và **gán** nhóm có sẵn | **CUSTOM_BACKEND** | AI Categorization/Smart Tags tham chiếu options, auto-update; có nguy cơ overwrite [S03]. Không tìm thấy bằng chứng policy "đủ tin cậy mới ghi quan hệ, không phá user-pinned" | Dùng 30 ghi chú Việt trộn chủ đề, 5 nhóm tồn tại, thử field AI; đếm correct **persisted** assignment sau reload, xem có tạo option sai/overwrite. **NOT_RUN** |
| **K06** — related items/backlinks | **NATIVE** (tham chiếu tay); AI auto-link **UNVERIFIED** | @Docs tạo backlink, Docs có linked references; Base có link fields và đề xuất record [S09, S06] | @link giữa 2 Docs; xóa một tham chiếu, xác nhận backlink thay đổi. Với hai record gần nghĩa kiểm **gợi ý hay tự liên kết**, lý do/vị trí dẫn chứng |
| **K07** — PDF/audio/video, nhảy trang/giây | **EXTENSION** | Minutes transcript có click-to-seek; PDF upload và gallery; chỉ video Minutes có transcript được embed trong Docs [S10, S11, S29] | Upload 1 PDF 5 trang, 1 MP3, 1 MP4 hợp lệ trên Pro; click trích PDF trang 3 và transcript ở 00:20, đo sai lệch. **Chưa đủ bằng chứng 1 UX xuyên mọi asset** |
| **K08** — nhiều lĩnh vực và nhiều view | **EXTENSION** | Base grid/kanban/calendar/gallery/Gantt/form, Wiki tree/shortcuts [S07, S30] | Một note thuộc 2 nhánh, 1 bản gốc, 5 views; sau edit ở view A, check view B/cây/ID. Mô hình 1 Item nhiều Topic như [C03] chưa được chứng minh thuần native |
| **K09** — Android+Windows+offline conflict | **UNVERIFIED** | Lark có Windows/Android; Docs mobile có offline edit/sync [S16, S17, S18] | Tạo note offline Android, sửa đồng thời Windows, reconnect, đối chiếu conflict. Riêng offline Base/Wiki/asset và Windows chưa có chứng cứ đủ mạnh |
| **K10** — API, MD+assets, backup/exit | **EXTENSION**; full fidelity **UNVERIFIED** | Docs desktop MD, Base CSV/XLSX/.base, SDK/API/MCP; Base export thiếu lịch sử/comments [S13, S14, S19–S23] | Export 100 notes+assets+Base relations+Wiki tree, kiểm SHA/reference/IDs, import sang **kho độc lập**, diff. Không hứa có backup khôi phục toàn bộ |
| **K11** — AI phân nguồn/trợ giúp vs tự sửa | **CUSTOM_BACKEND** | AI field tự điền có auto-update/overwrite, tham chiếu external model [S03]; policy dữ liệu [S24, S25] | Đặt source text, user edit, AI suggestion tách field; đổi source rồi đối chiếu không đổi user note, kiểm output có link+locator+model/version/chi phí. **NOT_RUN** |
| **K12** — >10k items, hàng trăm GB Drive | **UNVERIFIED** | Starter 2k rows/bảng, Pro 20k, Enterprise 50k; quota automation/storage [S12, S15] | Load 10.001 bản ghi và sample video; đo load/search/export/latency/quota; kiểm remote Google Drive có thể làm canonical storage mà không copy hay không. **Chưa có chứng cứ** |

**Không có hàng nào được đánh dấu PASS.** "NATIVE" nghĩa là tài liệu mô tả một phần chức năng có sẵn; chỉ có bài thử UI/API thực tế mới chuyển được thành PASS. Sự thiếu bằng chứng được ghi UNVERIFIED, **không tự gán NOT_SUPPORTED** trừ khi nhà cung cấp nói rõ (ví dụ Starter/Basic không có transcript Minutes [S11]; Base export không mang edit history [S14]).

## 4. So với mã đang chạy tại Kho Tri Thức — không đối chiếu với kế hoạch cũ

Những đánh giá "đã có" là **đã có mã ở main**; mức LIVE_PASS/NOT_RUN dựa trên CURRENT_STATE, không suy tự động sang Android hay mọi dữ liệu người dùng.

| Khả năng | Tình trạng mã/main | Lark học được gì; quyết định |
| --- | --- | --- |
| Receipt/duplicate/idempotency | **Đã có** CaptureEvent riêng với server_received_at, idempotency_key unique theo owner/channel; UI trả thời gian receipt [C01, C02]. CURRENT_STATE ghi backend/Windows live ở phạm vi đã thử [C08] | Lark không chứng minh cùng contract. **Giữ Django/PostgreSQL**, không thay bằng Base Created at |
| Nguồn URL/text/video + lưu Drive | **Đã có** Source/Item/Asset, worker, Google Drive adapter; Windows live đã tải 1 Reel và readback MP4 SHA. YouTube/TikTok diện rộng chưa nghiệm thu [C08] | Lark hấp dẫn với AI import fields, nhưng **không thay yt-dlp/metadata/Drive**; chỉ nghiên cứu UX paste |
| Bản văn bản chính và Markdown | **Đã có** Note nguyên văn, React Markdown+GFM, source HTML bị bỏ, URL an toàn, upload .md; Windows live kiểm bài công khai [C05, C08] | Docs editor/callout/tables/preview nhiều người dùng tốt hơn; **tham khảo giao diện**, không chuyển nguyên dữ liệu sang Lark Docs |
| Cây linh hoạt, một bài nhiều nhánh | **Đã có** Topic.parent và ItemTopic many-to-many, tree/đếm theo Item duy nhất, tránh chu trình; UI cây [C03, C06] | Wiki cho pattern breadcrumbs/shortcut/permission nhưng không có lý do viết lại cây. **Có thể cải thiện UX** |
| Gán nhóm thực, giữ user override | **Đã có mã** OrganizationService gán ItemTopic/Tag/Project nguồn auto hoặc user, method/source version, liên kết có reason. **Ngưỡng còn bảo thủ** và chất lượng corpus thật chưa nghiệm thu [C04, C08] | AI field shortcut gợi ý taxonomy; **không import kết luận như auto-label đã chính xác**. PoC riêng trên corpus công khai trước |
| RelatedItem với evidence | **Đã có mã** bảng RelatedItem và panel related [C03, C04, C07]. Tìm candidate qua PostgreSQL FTS, ngưỡng lexical rất thận trọng; chất lượng real corpus còn mở | Docs @backlinks minh bạch hơn cho **liên kết chủ động do người dùng tạo**. Bổ sung phân biệt Manual Link / Suggested Related, không nhân bản bài |
| Transcript & locator | **Đã có** DerivedContent.source_locator, processor/version/hash; Windows live ASR 1 Reel 11 đoạn tiếng Anh, nhãn cần rà; playback seek đúng giây **NOT_RUN** [C05, C08, C09] | Minutes click transcript là **UX mẫu**; cần đo sai lệch ±2 giây trước báo đạt, không tự suy transcript Việt |
| Search đa nguồn | **Đã có** SearchService/PostgreSQL FTS/trigram và hai GIN index theo dữ liệu; bài Việt thử trong phạm vi CI/Windows [C10, C08] | Lark view/filter là bổ sung cách trình bày, không thay search/query engine |
| Portable backup và restore | **Đã có** manifest v3 + backup Drive/Windows và restore DB thử 15 collection với SHA, còn các biến thể chưa thử [C08] | Lark .base/export thiếu history; đổi sang Lark làm khó bảo toàn. **Không đánh đổi invariant/restore** |
| Trải nghiệm Android/offline | **Chưa nghiệm thu Android thực**; PWA/Windows có mã và Windows live [C02, C08] | Docs mobile offline là gợi ý tốt; ưu tiên test PWA Android hiện tại rồi mới mở offline queue, tránh ghi đè server time |

**Nhận xét về người dùng cá nhân tại Việt Nam:** Lark có giao diện và bài help center tiếng Việt [S31], đa nền tảng, Docs rich text tốt. Tuy nhiên hỗ trợ dấu/Unicode qua sửa đồng thời, AI tiếng Việt, hoạt động Android chia sẻ URL, tốc độ tìm kiếm 10k+ mục và Minutes nhận giọng Việt là những **giả thuyết** phải đo. Nhiều phần Lark thiên về workspace/collaboration hơn là tiếp nhận video cá nhân với Drive đã có. Lark quốc tế và Feishu nội địa có tenant/endpoint tách nhau [S23], phải dùng đúng domain app/OAuth.

## 5. Chấm 7 trụ theo rubric G00

Điểm là **ước lượng nghiên cứu nguồn**, không phải benchmark; confidence thấp/trung bình/cao thể hiện độ mạnh của bằng chứng cho mục tiêu Kho Tri Thức. Khi thiếu test dùng khoảng độ nhạy, **không lấy UNVERIFIED = 0**.

| Trụ / tối đa | Điểm ước lượng | Độ tin cậy | Căn cứ và điểm bị trừ |
| --- | ---: | --- | --- |
| Capture + ingestion /20 | **10/20** | Trung bình | Paste text/ảnh và API record mạnh [S01, S20], nhưng URL media, receipt bất biến và duplicate semantics chưa chứng minh |
| Organization + recall /20 | **16/20** | Trung bình | Wiki, Base nhiều view, tags, related-links rất tốt [S03, S07, S09, S30], song phân loại có bằng chứng & tự ghi group như [C04] chưa chứng minh |
| Text editor + reading /15 | **13/15** | Cao cho chức năng, thấp cho roundtrip | Docs rich text, bảng, inline media và Markdown export [S08, S13]; chưa kiểm diff Unicode/asset |
| Provenance/related/timestamps /15 | **7/15** | Trung bình-thấp | Backlinks/Minutes timestamp mạnh [S09–S11] nhưng không có source locator xuyên loại file, version AI, CaptureEvent bất biến |
| Android/Windows/offline /10 | **7/10** | Trung bình | Có native clients và Docs mobile offline [S16–S18], các nhóm màn hình/collision chưa test |
| Portability/backup /10 | **5/10** | Trung bình | MD export và API có [S13, S19]; Base export mất history/comments [S14], tài liệu/asset không được chứng minh migrate lossless |
| Integration/cost/maintainability /10 | **5/10** | Trung bình | OpenAPI/SDK/MCP, nhiều hook [S20–S23]; row limits, giá/quota, closed SaaS và scope/OAuth [S12, S15] |

**Tổng tham chiếu: 63/100** (= 10+16+13+7+7+5+5); **khoảng nhạy cảm 52–70/100** nếu các phần NOT_RUN cho kết quả kém/tốt. Đây là **mức đáp ứng chức năng phổ thông** chứ không phải phần trăm sẵn sàng thay toàn hệ thống.

**Tách hai quyết định:**
- **Thay toàn bộ Kho Tri Thức:** **không khuyến nghị / phù hợp thấp**, vì không có chứng minh các invariant receipt/event, gốc Drive, provenance, restore/portability, tự trích nội dung URL media. Để thay phải chứng minh toàn bộ K01–K12 (đặc biệt K02/K03/K05/K10/K12) trên dữ liệu vô danh và chấp nhận migration.
- **Học tính năng:** **cao**, nhất là AI paste-to-fields, Smart Tags có vùng preview, multiview, Wiki tree/backlinks và click-seek của Minutes. Không cần tích hợp Lark hay dịch chuyển dữ liệu để áp dụng UX này.

## 6. Đề xuất 6 tính năng có thể học/tích hợp, không sửa code trong PR G03

Tất cả dưới đây là **ý tưởng có điều kiện**, không đồng nghĩa G03 đã triển khai hay được G00 duyệt. Độ khó S/M/L tương đối theo Django+React hiện tại.

| ID / độ khó | UX đề xuất | Adapter/kỹ thuật, phụ thuộc | Acceptance đo được / rủi ro |
| --- | --- | --- | --- |
| **L01 / M** — Paste-to-fields có preview | Dán khối text/ảnh vào màn gửi, màn hình liệt kê title/url/author/date **đề xuất** và nguồn trích từng field; người dùng xác nhận trước ghi | Thêm parser/adapter **tùy chọn** sau CaptureService, không chạm CaptureEvent; ảnh cần OCR có điều kiện, lưu provenance và không gọi field thiếu dữ liệu là đã hiểu video. Nguồn cảm hứng [S01, S02] | Corpus giả 30 input Việt/ảnh, ít nhất 27/30 đi đúng type và không sai source; **100% trường do người dùng sửa không bị AI ghi đè**; feature flag off vẫn nhận ghi chú đúng |
| **L02 / M** — Smart Tags chỉ trong taxonomy hiện có | Với một Item, xem 1–3 tag/topic ứng viên, evidence snippets, "Gắn"/"Bỏ qua"; nếu đủ tin cậy mới auto theo policy | Dùng OrganizationService/Tag hiện tại [C04]; thêm candidate provider đánh giá corpus, không cho AI tự tạo nhánh hàng loạt; input ưu tiên note + text thực, không dựa thumbnail/like | 50 case gán nhóm chuẩn do người đánh dấu; precision auto >= 90% trên tập chuẩn, không có user-pinned bị xóa, phép thử replay không nhân đôi assignment; thiếu text → Chưa phân loại |
| **L03 / S** — Nhiều chế độ xem trên cùng Item | Toggle Bài / Thẻ / Bảng / Theo ngày trong Thư viện, filter theo nhiều nhánh; nhớ lựa chọn trong UI | React views sử dụng API hiện tại, **không thêm bảng dữ liệu**; từ pattern Base [S30] | 1 Item trong 2 Topic chỉ có **1 ID** trên view toàn bộ, vẫn xuất hiện ở cả 2 bộ lọc; 4 views cùng danh sách/pagination; test 100% không đổi backend dữ liệu |
| **L04 / S–M** — Manual links + Backlinks | Nhập "Liên kết đến bài này" rồi hiện tab "Được nhắc đến" tách khỏi "Bài tương tự (tự đề xuất)" | Bổ sung relation_type/manual-origin hoặc adapter riêng trên RelatedItem với migration có kiểm; không trộn proposal với link người dùng. Pattern Docs [S09] | Tạo A→B, backlink trên B xuất hiện ngay; xóa A→B thì mất; refresh/restore vẫn chính xác; user-manual link không bị job auto làm stale |
| **L05 / M** — Trình xem nguồn kèm chứng cứ | Bên cạnh văn bản trích, hiện loại nguồn, processor/version, locator, cảnh báo AI; click trang PDF/mốc audio nếu có | Mở rộng KnowledgeReading từ DerivedContent.source_locator và đọc Asset, không tạo nội dung giả [C05, C09]. Pattern Minutes [S10] | 20 locator: trang/mốc đúng trong >=19/20; khi thiếu locator hiện "Không có mốc"; không hiện lời nói suy đoán chỉ từ metadata |
| **L06 / M** — Transcript click-to-seek | Highlight đoạn transcript đang phát, bấm đoạn nhảy player, giữ link theo thời gian | React player event + source_locator nếu transcript ASR có start/end; không thay processor; khối chức năng có thể dùng file công khai hiện có. Pattern Minutes [S10, S29] | Trên 10 đoạn transcript test có thời gian, seek sai lệch <=2 giây khi file có thể phát, không chạy ASR mới; nếu Drive preview chưa sẵn sàng báo rõ và không đánh dấu PASS |

**Không đề xuất:** dựng Base làm DB chính, chuyển hết MP4 sang Lark, cài Lark SDK/MCP cho bản đầu, tự đưa data thật vào third-party AI, tạo graph/vector DB chỉ để bắt chước UI. Các tính năng này trái nguyên tắc chi phí và invariants hiện có hoặc chưa có bằng chứng lợi ích vượt chi phí.

## 7. Rủi ro chính, phản chứng và phép thử đổi quyết định

1. **Mất tính di động và lịch sử:** Base CSV/.base không gồm edit history, comments, permission; Docs UI xuất Markdown nhưng API export công bố không tương đồng. Di trú sẽ phải có inventory, mapping ID, SHA asset và restore roundtrip [S13, S14, S19].
2. **Khóa gói/cost:** Starter 2.000 record/bảng; >10k cần thiết kế chia bảng hay trả Pro 20k/bảng, 50.000 automation runs/tháng; với 500 GB media phải xem hạn upload/storage và thời hạn ưu đãi [S12, S15, S27]. Giá $12 Pro tham chiếu niêm yết thanh toán năm, **không phải báo giá sau thuế tại Việt Nam**.
3. **AI không bảo vệ dữ liệu theo mặc định nghiệp vụ riêng:** Smart Tags auto-update/overwrite; API model ngoài cần key và chấp thuận xử lý dữ liệu; privacy policy có điều kiện cho phép training theo Workplace Owner [S03, S24, S25].
4. **Nhiều thành phần độc quyền:** Lark cloud document model và .base proprietary; MIT áp dụng SDK/MCP public chứ không giúp self-host SaaS. Dù có SDK/API, app scopes/quotas vẫn tồn tại [S14, S21–S23].
5. **Độ phủ ngôn ngữ & offline không kiểm:** mobile Docs offline có tài liệu, nhưng Windows offline/Android Share Target mọi URL, AI giọng Việt/Minutes, tranh chấp đồng bộ không có test ở lượt này [S11, S16–S18].
6. **Chưa chứng minh khả năng phát file lớn từ Google Drive đang dùng:** các thành phần Lark lưu file trong không gian và giới hạn theo plan; không có cơ sở coi remote Drive vừa là source of truth vừa giữ preview/time locator với 10.000+ Item.

**Giả thuyết phản chứng A:** Lark có thể thay phần lớn nếu một PoC hợp lệ với quyền admin cá nhân cho thấy, với ≥10.001 mục và bộ mẫu ≥100 URL/video/Docs, mọi ca K01–K12 đều đạt; export+restore giữ 100% source, event timestamps, label do người dùng, relations và toàn bộ asset/hash, chi phí 12 tháng được chấp nhận, không phụ thuộc việc rời Google Drive bất hợp lý. **Chưa có PoC này.**

**Giả thuyết phản chứng B:** Lark chỉ cần làm frontend/knowledge layer nếu có adapter API nhất quán, không phá ID/Drive, kéo được Markdown/timestamps/provenance và giảm đáng kể công bảo trì so với React. Cần chứng minh bằng một PoC **5–10 Item công khai**, diff 2 chiều trước/sau export, đo API quotas và phục hồi, rồi mới so tổng chi phí. **Chưa có.**

**Điều khiến hạ mức đánh giá:** kết quả test Unicode Việt/AI sai, mất liên kết hoặc asset khi export, metadata/giờ bị chỉnh sửa, sai lệch transcript, mobile offline xung đột hoặc chi phí vượt ngân sách. Khi đó chỉ tham khảo bố cục UX.

**Đề xuất chốt G03:** **THAM KHẢO UX**, thử riêng L01 hoặc L04/L06 trên dữ liệu công khai khi G00 chọn; **không thay thế nền tảng**, **không tích hợp SDK/CLI/MCP ngay**.

## 8. Checklist tái thử có trách nhiệm

Nếu sau này chủ sở hữu cho phép một workspace thử, chỉ dùng corpus giả hoặc dữ liệu công khai, không upload token, video cá nhân hoặc tài liệu nhạy cảm. Ghi từng ca K01–K12: tên plan, build/client version, Android/Windows version, thời gian địa phương và server, từng nút/ảnh bước, số lượng bản ghi thực, URL/response code khi API, thời gian nhận, SHA export/asset nếu có, log PASS/FAIL/NOT_RUN. Với Minutes ghi ngôn ngữ, định dạng, độ dài, vùng có lời và độ lệch giây. Với AI ghi rõ model/field shortcut, prompt/setting, auto-update, kết quả **đã được lưu** hay chỉ gợi ý. Với export phải thử **restore vào workspace khác** (không xem file tải xuống là bảo đảm có thể phục hồi).

## 9. Nguồn ngoài (truy cập 20/11/2026)

| Mã | Nguồn chính thức và bằng chứng chính |
| --- | --- |
| S01 | [Lark Help — Overview of AI features in Base](https://www.larksuite.com/hc/en-US/articles/708041262345-overview-of-ai-features-in-base): AI import chữ/ảnh, shortcuts, agent/workflow |
| S02 | [Lark updates](https://www.larksuite.com/hc/en-US/articles/360046836333-lark-updates): V7.67, ngày 2026-05-07 và release lịch sử |
| S03 | [Use AI field shortcuts in Base](https://www.larksuite.com/hc/en-US/articles/353219634284-use-ai-field-shortcuts-in-base): category, smart tags, reference options, auto-update và overwrite |
| S04 | [Triggers and actions for Workflow and Automations](https://www.larksuite.com/hc/en-US/articles/559049381351-triggers-and-actions-for-workflow-and-automations): trigger/hành động |
| S05 | [Use Workflow in Base](https://www.larksuite.com/hc/en-US/articles/641266732374-use-workflow-in-base): If/Else/Loop, khác automation |
| S06 | [Lark: AI and linking records — overview Vietnamese](https://www.larksuite.com/hc/vi-VN/articles/708041262345-t%E1%BB%95ng-quan-v%E1%BB%81-c%C3%A1c-t%C3%ADnh-n%C4%83ng-ai-trong-base): AI gợi ý record liên quan |
| S07 | [Get started with Wiki](https://www.larksuite.com/hc/en-US/articles/360048488377-get-started-with-using-wiki): cấu trúc trang/permissions |
| S08 | [Get started with Docs](https://www.larksuite.com/hc/en-US/articles/560483946591-get-started-with-docs): Markdown shortcut, bảng, files, embeds |
| S09 | [Use @ feature in Docs](https://www.larksuite.com/hc/en-US/articles/474099263964-use-the-%40-feature-in-docs): @document và backlink |
| S10 | [Get started with Minutes](https://www.larksuite.com/hc/en-US/articles/735200985222-get-started-with-lark-minutes): click transcript → playback, search |
| S11 | [Generate Minutes for meetings](https://www.larksuite.com/hc/en-US/articles/379706923950-generate-minutes-for-meetings): Pro/Enterprise, file 4 GB, 16 giờ |
| S12 | [Lark plans — Việt Nam](https://www.larksuite.com/vi_vn/plans): plan, giá, lưu trữ, upload |
| S13 | [Download documents or folders](https://www.larksuite.com/hc/en-US/articles/459605932895-download-documents-or-folders-to-your-device): Docs Markdown desktop, formats |
| S14 | [Import or export a Base](https://www.larksuite.com/hc/en-US/articles/981789591541-import-or-export-a-base): .base/CSV/XLSX, thiếu history/comments, import limits |
| S15 | [Overview paid features for Base — VI](https://www.larksuite.com/hc/vi-VN/articles/843573886007-t%E1%BB%95ng-quan-v%E1%BB%81-c%C3%A1c-t%C3%ADnh-n%C4%83ng-tr%E1%BA%A3-ph%C3%AD-cho-base): rows/runs theo gói |
| S16 | [Download/install Lark client](https://www.larksuite.com/hc/zh-CN/articles/360047182373-%E4%B8%8B%E8%BD%BD%E5%92%8C%E5%AE%89%E8%A3%85-lark-%E5%AE%A2%E6%88%B7%E7%AB%AF): Windows/Android và các hệ điều hành |
| S17 | [Make Docs editable offline — mobile VI](https://www.larksuite.com/hc/vi-VN/articles/496250991888-l%C3%A0m-cho-docs-c%C3%B3-th%E1%BB%83-ch%E1%BB%89nh-s%E1%BB%ADa-ngo%E1%BA%A1i-tuy%E1%BA%BFn-tr%C3%AAn-di-%C4%91%E1%BB%99ng): offline mobile |
| S18 | [View/restore Docs edit history](https://www.larksuite.com/hc/en-US/articles/904560370164-view-and-restore-edit-history-in-docs): local edit records; không export edit history |
| S19 | [Lark Open Platform — Drive export task](https://open.larksuite.com/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/export_task): docx/pdf API, giới hạn export |
| S20 | [Open Platform — Base overview API](https://open.larksuite.com/document/server-docs/docs/bitable-v1/bitable-overview): records/tables/fields API |
| S21 | [Open Platform — Docx blocks API](https://open.larksuite.com/document/server-docs/docs/docs/docx-v1/docx-overview): create/list/update blocks |
| S22 | [GitHub larksuite/oapi-sdk-python](https://github.com/larksuite/oapi-sdk-python): Python SDK MIT; không phải mã nguồn SaaS |
| S23 | [GitHub larksuite/lark-openapi-mcp](https://github.com/larksuite/lark-openapi-mcp): official MCP beta, limits; và [larksuite/cli](https://github.com/larksuite/cli) command/skills, đọc README chứ không cài |
| S24 | [Lark Privacy Policy](https://www.larksuite.com/privacy-policy): workplace info và AI training theo ủy quyền |
| S25 | [Lark Service Specific Terms](https://www.larksuite.com/service-specific-terms): dữ liệu AI input/output/permissions |
| S26 | [Admin — Edit organization info](https://www.larksuite.com/hc/en-US/articles/005814481026-admin-edit-organization-info): data residency tại tạo tổ chức |
| S27 | [Use AI-generated text in Workflow and Automations](https://www.larksuite.com/hc/en-US/articles/342639491034-use-ai-generated-text-in-workflow-and-automations): quota AI miễn phí tạm thời |
| S28 | [Use fields in Base](https://www.larksuite.com/hc/en-US/articles/364163852421-use-fields-in-base): Created at/Last update/Hyperlink/Attachment |
| S29 | [Embed Minutes videos in Docs](https://www.larksuite.com/hc/en-US/articles/392861255933-embed-minutes-videos-in-docs): transcript trong embedded player |
| S30 | [Use views in Base](https://www.larksuite.com/hc/en-US/articles/360048488184-use-views-in-base): grid/kanban/calendar/gallery/Gantt/form |
| S31 | [Lark Help — AI Base tiếng Việt](https://www.larksuite.com/hc/vi-VN/articles/708041262345-t%E1%BB%95ng-quan-v%E1%BB%81-c%C3%A1c-t%C3%ADnh-n%C4%83ng-ai-trong-base): tài liệu giao diện VI |
| S32 | [Base workflow/automation FAQs](https://www.larksuite.com/hc/en-US/articles/126710842099-base-workflow-and-automations-faqs): log hoạt động 7 ngày, quota runs |

## 10. Mã nguồn đối chứng Kho Tri Thức (main SHA nêu đầu báo cáo)

| Mã | Link code hoặc vận hành; không thay báo cáo live bằng suy luận |
| --- | --- |
| C01 | [ingestion/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/ingestion/models.py) — CaptureEvent/idempotency |
| C02 | [web/CaptureScreen.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/CaptureScreen.tsx) — receipt/Markdown/upload |
| C03 | [catalog/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/models.py) — Item/Topic/Assignment/RelatedItem |
| C04 | [catalog/organization.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/organization.py) và [organization_job.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/organization_job.py) — gán nhóm và ngưỡng |
| C05 | [web/KnowledgeReading.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeReading.tsx), [web/KnowledgeText.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeText.tsx) — Markdown/text nguồn |
| C06 | [catalog/knowledge_tree.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/catalog/knowledge_tree.py) và [web/KnowledgeTree.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/KnowledgeTree.tsx) |
| C07 | [web/ItemOrganization.tsx](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/web/src/ItemOrganization.tsx) — nhóm và related panel |
| C08 | [docs/CURRENT_STATE.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/CURRENT_STATE.md) — evidence Windows/CI/restore và NOT_RUN |
| C09 | [processing/models.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/processing/models.py) — DerivedContent.source_locator, processor |
| C10 | [search/services.py](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/apps/backend/search/services.py) — SearchService |

**Kiểm tra độc lập:** không đọc G00-INITIAL-SOURCES.md; không đọc G01–G17 reports; không chỉnh mã, MASTER_PLAN hay CURRENT_STATE. **Checkpoint: REPORT_READY / DOCUMENT_RESEARCH, LIVE_PRODUCT_TESTS_NOT_RUN; chờ G00 review, không tự nhận toàn ứng dụng PASS.**
