# G00 — TỔNG HỢP SO SÁNH 17 ỨNG DỤNG VÀ ĐỀ XUẤT ƯU TIÊN

**Ngày tổng hợp và rà soát lần hai:** 20/11/2026. **Loại:** kết luận nghiên cứu và **đề xuất** thứ tự backlog G00, chưa phải chấp thuận của người dùng hay nghiệm thu mã mới.  
**Nguồn:** 17 báo cáo độc lập [G01–G17](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/INDEX.md), mỗi báo cáo tại PR tương ứng; [biên bản đối chiếu nguồn G00](G00-INDEPENDENT-AUDIT.md); [hiện trạng ứng dụng](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/CURRENT_STATE.md).  
**Khuyến nghị trọng tâm G00:** **GIỮ** Kho Tri Thức Django/PostgreSQL/Google Drive và ID/sự kiện nguồn hiện tại. **XEM XÉT NÂNG CẤP** trải nghiệm văn bản, nhận nhanh, đọc nguồn có locator và tổ chức tri thức, theo PoC nhỏ có đo nghiệm thu; **KHÔNG KHUYẾN NGHỊ** thay toàn hệ thống bằng một ứng dụng ghi chú. Đây là khuyến nghị kỹ thuật, chưa phải phê duyệt triển khai.

## 1. Lý do không thay nền tảng (cổng phủ quyết độc lập với điểm)

Muốn thay Kho Tri Thức, sản phẩm phải chứng minh đồng thời:
1. Biên nhận cho từng lần gửi (CaptureEvent không mất), gửi mới ≠ retry cùng idempotency key; lịch sử raw input truy hồi được.
2. Video/tài liệu gốc nằm tại Google Drive theo asset_id/item_id nội bộ, upload/readback SHA, không mất nguồn khi phân loại hay AI lỗi.
3. Cây nhiều tầng không đồng độ sâu, một bài nhiều nhánh nhưng một ID; tự gán nhóm có chứng cứ và giữ user-pinned, không auto-merge hai note gần nghĩa.
4. Tra cứu văn bản và nguồn có version/locator; phân biệt người viết với text/AI; export-backup/restore; Windows và Android sử dụng được.
5. Dữ liệu mục tiêu trên 10.000 mục và hàng trăm GB video: có phép thử quy mô hoặc đường mở rộng rõ ràng (K12 hiện đa số NOT_RUN).

Không báo cáo G01–G17 nào đưa ra bằng chứng vượt tất cả năm gate này. Kết luận **không thay toàn bộ** là từ việc thiếu chứng cứ đạt gate, KHÔNG có nghĩa các sản phẩm khác kém hoặc Kho Tri Thức hiện đã PASS đủ năm gate (Android/K12 còn NOT_RUN).

## 2. Bảng so sánh 17 sản phẩm — giữ nguyên điểm tác giả, không tạo xếp hạng giả

**Quy ước:** cột điểm là **ước lượng theo tài liệu của từng luồng**, giữ khoảng khi tác giả không chấm điểm giữa; không phải thước đo hiệu năng, không thể so tuyệt đối và không thể cộng trung bình 17 sản phẩm. Dấu veto về nhà cung cấp/kiến trúc là điều kiện riêng, không bị điểm cao vô hiệu hóa.

| Luồng/sản phẩm | Điểm tác giả /100 (khoảng nếu có) | Năng lực đáng học | Quyết định G00 |
| --- | --- | --- | --- |
| [G01](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) Notion | 61 (50–75) | Block editor, relations, saved database views | Chỉ tham khảo UX; không dùng làm lõi Drive/event |
| [G02](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) Google Keep | 37–54 | Capture cực nhanh, pin, label, Android share | Tham khảo UX capture; labels 50 không đủ taxonomy |
| [G03](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) Lark | 63 (52–70) | Paste-to-fields, AI categorization, wiki/views | PoC UX fields; không suy auto-video |
| [G04](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) Evernote | 54–74 | Web clipper, OCR/semantic, AI edit review, PDF | Tham khảo clipper+review; dữ liệu SaaS và export hạn chế |
| [G05](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) OneNote | 56 (42–67) | Ghi chú liên kết thời điểm audio, freeform page | PoC note-linked locator; không mang nền tảng sang |
| [G06](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) Apple Notes | 50 (39–62) | Quick Notes, scan, Markdown import/export | Tham khảo share UI; Android/Windows không tương đương |
| [G07](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) Mem.ai | 62 (52–70) | Related Heads Up, collections, diff/accept | NO-GO nhà cung cấp (đóng 15/01/2027); chỉ học UX |
| [G08](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) Coda / Superhuman Docs | 59 (48–70) | Connected multi-view, formula, button workflow | Tham khảo nhiều view; AI/database còn beta |
| [G09](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) Reflect Open | 59 (51–68) | Markdown-first, daily notes, wikilinks/backlinks | Tham khảo editor/kiến trúc file; Android chưa có |
| [G10](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) Superpowered | 15–18 | Meeting templates/AI notes | NO-GO tích hợp: trang tải ngừng cung cấp |
| [G11](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) Gemini Notebook | 60 (53–67) | Grounded citation, research source, API/MCP preview | Tham khảo cite-to-source; không làm kho chính |
| [G12](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) AFFiNE | 61 (46–75) | Page/Edgeless, block canvas, backlinks | PoC editor cô lập nếu phù hợp license; không fork |
| [G13](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) Capacities | 66 (48–81) | Object types, source highlights, related view; **audio ghi/phiên âm/tóm tắt đã có trong Pro (11/2026)** | Tham khảo UX type/links và audio; không suy ra AI hiểu toàn video |
| [G14](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) Tana Outliner | 53–71 | Supertags, live queries, reusable nodes | Mượn loại bài/metadata nhẹ; không đổi toàn schema |
| [G15](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) Granola | 56 (44–67) | Raw note + AI suggestion, transcript source | Tham khảo phân biệt 2 lớp; không có audio gốc |
| [G16](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) Heptabase | 71 (57–85) | Source cards, PDF highlights, context citations | PoC link đến nguồn; kiểm seek MP4 thực |
| [G17](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) Obsidian | 64 (54–72) | Live Preview Markdown, backlinks, Bases | Đối chứng ưu tiên cho UX văn bản; không dùng backend video |

**Phản biện chéo có kết luận:** (a) Heptabase 71 và Capacities 66 không thắng yêu cầu backend Drive/video + CaptureEvent; (b) Mem 62 vẫn NO-GO vì dịch vụ đóng; (c) Obsidian 64 được ưu tiên làm mẫu **editor** nhờ Markdown/Live Preview chứ không phải lựa chọn **backend**; (d) khả năng API/MCP beta của Gemini Notebook không tương đương sao lưu/khôi phục và quyền mọi tài khoản; (e) AI nhập field của Lark không chứng minh tự đọc mọi video.

## 3. Kiểm tra khoảng trống đúng theo mã main hiện hành

| Nghiệp vụ | Đã có (không xây lại) | Khoảng trống thực sự cần cải thiện |
| --- | --- | --- |
| Lưu bản viết và đọc Markdown | Item.note, ItemScreen Textarea; KnowledgeText với react-markdown/remark-gfm, skipHtml | Trải nghiệm Live Preview/split/shortcut/undo và UX soạn dài, cần PoC editor |
| Tiếp nhận/link chia sẻ | CaptureService/receipt/idempotency; manifest.webmanifest đã có share_target; sharedCapture.ts; CaptureScreen | Android share thực chưa nghiệm thu; tối ưu số thao tác/preview và thông báo offline |
| Gán nhóm & nội dung liên quan | KnowledgeTree, Topic M:N, RelatedItem; ItemOrganization/RelatedItems | Trực quan hóa liên kết ngược, lý do liên quan và jump-to-context; không tạo graph DB |
| Đọc nguồn | ReadKnowledgeService và DerivedContent.locator; KnowledgeReading đã hiển thị trang/section và nút xem asset | Locator cần khả năng bấm **mở đúng trang/giây** và giữ provenance/version; không chỉ chữ mô tả |
| Danh sách trong thư viện | LibraryScreen có cây, bộ lọc và danh sách | Chưa có các chế độ xem Bảng/Thẻ/Timeline dùng cùng Item ID/filter |
| AI biên tập | Text gốc và nguồn trích được tách; phân nhóm hiện tại dựa quy tắc/lexical | Nếu bổ sung AI phải có preview/diff/accept, lý do, quyền và rollback; không ghi đè tự động |
| Backup/Drive | Đã có adapter, backup/restore và pilot có chứng cứ theo CURRENT_STATE | Không viết lại chỉ vì đối thủ có export; kiểm K12, Android và host/client thay đổi trước khi mở rộng |

## 4. Danh mục ưu tiên G00 — loại trùng lặp giữa 17 đề xuất

**Các mức dưới đây chỉ xếp thứ tự các ý tưởng UX rút ra từ 17 nghiên cứu** (không phải mức ưu tiên chung của toàn dự án): P0 = PoC UX sớm **sau khi không ảnh hưởng các gate dữ liệu/ingest/Android**, P1 = sau P0, P2 = tùy nhu cầu, HOÃN = chưa tạo task code. S/M/L chỉ là độ khó tương đối; chưa được người dùng phê duyệt và chưa phải cam kết PASS.

| ID / mức | Quyết định & lý do | Nguồn ý tưởng | Phạm vi tối thiểu — không phát sinh hệ thống song song | Tiêu chí nghiệm thu đề nghị |
| --- | --- | --- | --- | --- |
| UX-01 / **P0, M** | **Editor Markdown Live Preview**: người dùng biên soạn nội dung là trung tâm; giữ raw markdown | G17 Obsidian, G09 Reflect, G12 AFFiNE, G01 Notion | Trước khi đổi thư viện, so sánh 3 hướng: **Textarea hiện có + bổ sung split preview (chưa có)**, CodeMirror 6, một editor theo ProseMirror (ví dụ Tiptap/Milkdown); không chuyển backend. Chế độ Edit / Edit+Preview / Read; bàn phím, phím tắt, IME tiếng Việt, GFM, link, XSS | 40 note tiếng Việt/bảng/link; mở-lưu-khôi phục **40/40 không mất dữ liệu ngoài chỉnh sửa chủ ý**; undo/redo; IME Unikey/EVKey; không đưa raw HTML nguy hiểm vào DOM; so đo trên Windows Full HD và Android |
| UX-02 / **P0, M** | **Click citation/source để tới đúng vị trí**: lợi ích cốt lõi khi học từ PDF/video | G16 Heptabase, G11 Gemini Notebook, G05 OneNote | Tái dùng DerivedContent.locator/source_version, player/asset hiện tại; làm nút tới nguồn, PDF page/segment/time; hiện trạng thái chưa có locator, không bịa timestamp | Bộ ít nhất 30 locator có nhãn gốc (PDF/web/audio/video); **30/30 mở đúng asset và vị trí logic**; video seek sai lệch <=1s ở tệp/codec được công bố; thiếu transcript ghi UNVERIFIED, không tự suy |
| UX-03 / **P0, S–M** | **Hoàn thiện Quick Capture và Android Share Target** thay vì xây mới share target | G02 Keep, G06 Apple Notes, G09 Reflect | Hiện manifest + readSharedCapture đã có; chỉ tối giản số thao tác, preview receipt và nghiệm thu trên thiết bị Android. Không đổi CaptureEvent | 30 lượt share note/link tiếng Việt: nhập→biên nhận đúng nguồn 30/30; hai lượt gửi thật = hai Event, retry cùng key không tăng Event; mất mạng không báo đã lưu |
| UX-04 / **P1, S–M** | **Panel liên quan/backlinks theo ngữ cảnh**; làm rõ mối quan hệ, không tự bịa link | G07 Mem Heads Up, G13 Capacities, G17 Obsidian | Tái sử dụng RelatedItems/ItemTopic đang có; bổ sung chiều được liên kết tới, cùng nhóm và reason; không thêm neo đồ thị mới nếu chưa cần | Fixture 30 Item, backlink có nguồn/phiên bản; 100% link tới ID đúng, không tạo kết quả không có chứng cứ; keyboard & màn hình nhỏ |
| UX-05 / **P1, M** | **Nhiều chế độ xem cùng dữ liệu**: Cây/Danh sách/Bảng/Thẻ/Timeline | G01 Notion, G08 Coda, G12 AFFiNE, G14 Tana | View state + filter/sort trên Item API hiện có, không sao chép Item, tách saved_at khỏi published_at | Seed 10.000 Item *giả lập* và nhiều nhánh; mọi view trả cùng tập Item ID sau filter, không nhân bản media; kiểm pagination và hiệu năng |
| UX-06 / **P1, M** | **Bản AI gợi ý riêng + duyệt diff** để không ghi đè tri thức người dùng | G04 Evernote, G07 Mem, G15 Granola | Chưa bật API AI mới ở nghiên cứu. Sau khi có nguồn và quyền, tạo suggestion/version/diff/reject/accept có kiểm soát | Không lệnh AI nào tự đổi Item.note; 20 ca edit có before/after, 100% chỉ thay sau accept; rollback/version giữ nguồn; có chế độ không dùng AI |
| UX-07 / **P1, S–M** | **Source cards nhỏ cạnh bài** (web/PDF/video, tình trạng bằng chứng) | G16 Heptabase, G12 AFFiNE, G04 Evernote | Dùng Source/Asset/DerivedContent, hiển thị metadata/thumbnail/locator đã có; không di chuyển MP4 | 20 nguồn với mapping đúng source_id/asset_id và version; **một nguồn có thể có nhiều asset/phiên bản hợp lệ** theo schema, không áp quy tắc 1–1; thiếu text hiển thị rõ; URL ngoài được lọc, Drive readback không bị ảnh hưởng |
| UX-08 / **P2, S–M** | **Template và thuộc tính theo loại bài** (bài học, sách, cuộc họp, nguồn video) | G14 Tana, G13 Capacities, G10 Superpowered | Chỉ tạo mẫu Markdown/metadata tùy chọn trên Item hiện có; không chuyển toàn hệ thống thành graph/outliner | 3 mẫu, 30 Item; áp/xóa template không ghi đè note/nguồn; có thể xuất văn bản chuẩn |
| UX-09 / **HOÃN, L** | Canvas/whiteboard vô hạn, fork AFFiNE/Obsidian, graph DB, API trả phí mới, ASR hàng loạt, bot meeting | G12/G16/G15 và các luồng liên quan | Không có nhu cầu/đo kiểm đủ mạnh so với chi phí; ghi trigger cụ thể mới mở | Chỉ nghiên cứu lại khi người dùng thể hiện nhu cầu và P0/P1 đạt gate; không mở issue code trước |

**Không nhân đôi dự án ghi âm cuộc họp:** Kho Tri Thức chỉ cần biết tiếp nhận bản ghi/tóm tắt/locator có nguồn; khả năng gõ trong khi ghi và seek audio tương tác chuyên sâu nên tái sử dụng hoặc nối adapter với ứng dụng họp riêng khi có yêu cầu rõ, không âm thầm tạo hai recorder.

## 5. Gate vận hành ưu tiên trước việc làm đẹp UI — tránh nhầm P0 UX với P0 hệ thống

**Đây là hiệu chỉnh quan trọng của lần kiểm toán thứ hai:** nhu cầu gốc là lưu, tổ chức và truy cập **hơn 10.000 mục/video** đáng tin cậy, còn các ý tưởng editor/backlink/whiteboard chỉ là một nhánh nâng cấp. P0 UX không tự vượt trước các điều kiện an toàn sau:

| Gate toàn hệ thống | Hiện trạng kiểm được ở main | Việc cần kiểm trước mở rộng người dùng | Quan hệ với UX |
| --- | --- | --- | --- |
| **CORE-01: Lưu trữ và khôi phục không mất dữ liệu** | Có PostgreSQL/Drive, upload/readback/backup-restore với các ca đã thử | Kiểm khôi phục corpus lớn, SHA/Drive access khi đổi host, client/project, lỗi upload/retry; không lấy pilot nhỏ làm minh chứng 10.000 video | **Chặn phát hành**, không chặn PoC UI cô lập |
| **CORE-02: Thu thập video đa nguồn** | Facebook Reel đã có live proof, parser/source worker từng phần; YouTube/TikTok còn khác biệt theo URL/quyền/môi trường | Test link chính chủ/công khai, timeout, quyền truy cập, file > ngưỡng upload, không dùng metadata để nhận định đã có media hay transcript | Cần trước trải nghiệm video phổ cập |
| **CORE-03: Android/Windows thật** | Windows có live acceptance; Android chưa có UAT thực | Test Android share target, reload, font/IME tiếng Việt, mạng chập chờn, video playback/seek trên thiết bị thật | UX-03 vừa là ý tưởng UX vừa là một phần gate |
| **CORE-04: Tốc độ và tính toàn vẹn nhóm** | Cây/RelatedItem/auto group đã có ở quy mô thử nhỏ | Kiểm 10.000 Item với nhiều nhánh, không làm sai pinned/quan hệ, cách tính tỷ lệ chính xác = đúng/tổng được gán nhãn; trường hợp thiếu nhãn = NOT_RUN | UX-04/05 chỉ cải tiến khả năng nhìn thấy/truy cập |

**Phạm vi:** đây là gate **đánh giá chất lượng/vận hành**, không tự ý khởi động ASR/OCR/vector hoặc mở thêm backend. Các mốc, điều kiện nghiệm thu chính thức vẫn ở ROADMAP_AND_TESTS và CURRENT_STATE; không tự chuyển thành PASS.

## 6. Ma trận ưu tiên và quy trình ra quyết định

- **Mức giá trị:** P0 là hai nhu cầu trực tiếp từ người dùng (văn bản/nguồn) và luồng tiếp nhận nhanh; P1 tăng hiệu quả đọc và tổ chức nhưng phụ thuộc tầng nguồn/editor; P2 là tùy chọn; HOÃN khi độ phức tạp cao hoặc một tính năng khác đã làm.
- **Mức bằng chứng:** tất cả đề xuất UX đều đã có mô tả/tài liệu nhà cung cấp; **chưa có kết quả PoC trên ứng dụng Kho Tri Thức**, do đó không được chuyển thành DONE hay PASS.
- **Nguyên tắc công thức nếu sau này lượng hóa ưu tiên:** mọi chỉ tiêu phải có cách tính và nêu trường hợp NOT_RUN; chưa tạo score chính xác giả vì chưa có thời gian triển khai, dữ liệu thao tác, chi phí/latency theo thiết bị. Không xếp hạng lấy trung bình 17 điểm nhà cung cấp.
- **Thứ tự đề xuất:** UX-01 và UX-02 cùng nhóm ưu tiên đầu; UX-03 kiểm nghiệm Android trên code sẵn có; sau đó UX-04/05/06/07, rồi UX-08. Không bắt một luồng phải chờ thư viện/PR khác: thiết kế adapter/fixture cô lập.

## 7. Những điều KHÔNG thay đổi và bước nghiệm thu tiếp theo

- Không sửa MASTER_PLAN, ROADMAP_AND_TESTS hoặc CURRENT_STATE chỉ vì báo cáo tham khảo. Nếu G00 được giao lập trình sau quyết định, lúc ấy mở task đúng roadmap + cập nhật điều kiện acceptance.
- Không merge 17 PR nguồn, không force-push, không sửa báo cáo các luồng, không công bố hệ thống đã chạy Android.
- Không chuyển PostgreSQL sang SQLite, Drive sang SaaS notes/Obsidian vault, hay ghi đè raw note bằng AI; bảo vệ UUID, CaptureEvent, event timestamp, video gốc, backup.
- Nếu muốn dùng thư viện editor, phải **so sánh 2–3 phương án và kiểm tra license** trước khi chốt theo AGENTS.md. Bước này là gate của UX-01, không coi kết luận tham khảo từ G17/G12 là cho phép sao chép code.
- Kết quả nghiên cứu G00 hiện chốt được **hướng kiến trúc, loại nhà cung cấp rủi ro, backlog ưu tiên và tiêu chí thử**; việc viết code/UI, chạy UAT Android, benchmark 10.000 mục là **giai đoạn triển khai riêng**, không thể giả PASS trong nghiên cứu.

**Hiệu chỉnh lần hai:** Kiểm lại tài liệu **Capacities Release 71/73**: audio recording, transcription và AI summary đã có cho gói Pro từ 11/2026; văn bản G13 gốc nói đúng, chỉ G00 bản trước sai. **Reflect Open** có Windows/Linux experimental unsigned theo README mới, nhưng Android không hỗ trợ; không dùng blog ra mắt tháng 7 làm trạng thái tháng 11. **Superpowered không còn cho tải bộ cài** không đồng nghĩa công ty chắc chắn đóng cửa hoặc tài khoản cũ hết hoạt động. **Khoảng điểm là đánh giá tài liệu**, không phải chỉ số sẵn sàng sản xuất; đối chiếu phép cộng 7 trụ khớp ở 17 báo cáo (G02/G04/G10/G14 dùng cận dưới). Đã loại giả định baseline có sẵn *split preview* và quy tắc mỗi nguồn chỉ có một asset.

**Trạng thái kết luận:** SYNTHESIS_RECHECKED / PRIORITY_PROPOSED_NOT_APPROVED / NO_CODE_CHANGED / NO_MERGE / PRODUCT_UAT_NOT_RUN. Các đề xuất chưa trở thành quyết định thay đổi code hoặc mua dịch vụ khi chưa được người dùng chọn triển khai.
