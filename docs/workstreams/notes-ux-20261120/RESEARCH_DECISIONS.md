# G00 — TÓM TẮT NGHIÊN CỨU ĐÃ CHỈNH SAI ĐỂ GIAO TRIỂN KHAI (MAIN)

**Ngày khóa thông tin:** 20/11/2026 (GMT+7). **Trạng thái:** RESEARCH_DIGEST / NOT_RUNTIME_PASS.  
**Nguồn chi tiết đã thẩm định:** [G00 PR #47](https://github.com/cavoixanh638/kho-tri-thuc/pull/47) (hai file `G00-INDEPENDENT-AUDIT.md` và `G00-CROSS-APP-DECISION.md`, **chưa merge**); nghiên cứu độc lập G01–G17 tại PR #30–#46 (**chưa merge**). Nội dung dưới đây có chủ đích ngắn và nằm ngay trên main để AI triển khai **không cần đoán kết luận**.

## 1. Phương pháp diễn giải

- Các điểm 100 trong báo cáo tác giả là **ước lượng mức phù hợp theo tài liệu**, không phải benchmark, điểm test hay xếp hạng khách quan giữa sản phẩm. Cộng bảy trụ trong 17 báo cáo khớp về mặt số học, nhưng **không** chứng minh sản phẩm điểm 71 tốt hơn sản phẩm điểm 64 ở mọi nhu cầu.
- **Điều kiện phủ quyết thay toàn hệ thống:** không có sản phẩm nào chứng minh đủ CaptureEvent bất biến/retry, Drive lưu nguồn theo ID nội bộ/SHA, cây nhiều nhánh tự gán có bằng chứng, xuất/restore toàn bộ, Windows+Android và khối lượng >10.000 Item/hàng trăm GB video.
- **Giữ kiến trúc và dữ liệu:** Django/PostgreSQL/Google Drive; khi học UX không được ghi đè note do người dùng viết, source, CaptureEvent hoặc user-pinned. Không tự chọn framework mới chỉ vì UI sản phẩm đẹp.

## 2. Ma trận toàn bộ 17 luồng (chỉ dùng định hướng feature)

| Luồng | Sản phẩm | Điểm tài liệu /100 (khoảng) | Giá trị UX/kiến trúc có thể học | Ranh giới / kết luận |
| --- | --- | --- | --- | --- |
| [G01/#43](https://github.com/cavoixanh638/kho-tri-thuc/pull/43) | Notion | 61 (50–75) | Block editor, database views/relations, clipper | Không thay Drive/event, export không mặc nhiên lossless |
| [G02/#42](https://github.com/cavoixanh638/kho-tri-thuc/pull/42) | Google Keep | 37–54 | Android quick capture, pin/labels/share | Giới hạn 50 labels; không thay cây Topic sâu |
| [G03/#45](https://github.com/cavoixanh638/kho-tri-thuc/pull/45) | Lark | 63 (52–70) | Paste text/image to fields, AI categorization, wiki | Field autofill không chứng minh tải/hiểu video tự động |
| [G04/#46](https://github.com/cavoixanh638/kho-tri-thuc/pull/46) | Evernote | 54–74 | Clipper, AI diff review, OCR, audio notes | SaaS, export ENEX/HTML và phí; không có CaptureEvent riêng |
| [G05/#40](https://github.com/cavoixanh638/kho-tri-thuc/pull/40) | OneNote | 56 (42–67) | Page tự do, note gắn thời điểm ghi audio trên Windows | Không suy sang Android/web; không thay lưu trữ media Drive |
| [G06/#41](https://github.com/cavoixanh638/kho-tri-thuc/pull/41) | Apple Notes | 50 (39–62) | Quick Notes/Share, rich note, Markdown import/export | Native Android không tương đương; chưa test round-trip đủ assets |
| [G07/#38](https://github.com/cavoixanh638/kho-tri-thuc/pull/38) | Mem.ai | 62 (52–70) | Related Heads Up, collections, diff/accept | **Không phụ thuộc dịch vụ:** công bố đóng 15/01/2027 |
| [G08/#36](https://github.com/cavoixanh638/kho-tri-thuc/pull/36) | Coda / Superhuman Docs | 59 (48–70) | Connected multiple views, automation, relation | Đổi tên 08/07/2026, các tính năng AI/database beta khác nhau |
| [G09/#34](https://github.com/cavoixanh638/kho-tri-thuc/pull/34) | Reflect Open | 59 (51–68) | Local Markdown, live preview, backlinks | Windows/Linux **experimental unsigned**, Android không hỗ trợ |
| [G10/#39](https://github.com/cavoixanh638/kho-tri-thuc/pull/39) | Superpowered | 15–18 | Meeting template và note workflow | Trang tải không còn bộ cài; không suy công ty đã đóng |
| [G11/#44](https://github.com/cavoixanh638/kho-tri-thuc/pull/44) | Gemini Notebook | 60 (53–67) | Citation đến đoạn nguồn, grounded research | API/MCP Public Preview, nguồn YouTube chủ yếu transcript |
| [G12/#32](https://github.com/cavoixanh638/kho-tri-thuc/pull/32) | AFFiNE | 61 (46–75) | Block/canvas/backlinks, local-first | Từng package có license riêng; tránh fork cả app |
| [G13/#37](https://github.com/cavoixanh638/kho-tri-thuc/pull/37) | Capacities | 66 (48–81) | Object/type, backlinks, PDF highlights, audio transcription | **Audio đã ra mắt Pro 11/2026**; vẫn chưa chứng minh AI phân tích toàn video; tệp tối đa 100MB |
| [G14/#33](https://github.com/cavoixanh638/kho-tri-thuc/pull/33) | Tana Outliner | 53–71 | Supertag, live queries, reusable nodes | Không thay PostgreSQL/schema Event/Drive; khác tana.inc họp |
| [G15/#31](https://github.com/cavoixanh638/kho-tri-thuc/pull/31) | Granola | 56 (44–67) | Raw note + AI enhanced, transcript linked | Không giữ audio gốc nên không thể dùng làm playback âm thanh nguyên bản |
| [G16/#35](https://github.com/cavoixanh638/kho-tri-thuc/pull/35) | Heptabase | 71 (57–85) | Source cards, PDF/YouTube highlights và locator | Không có bằng chứng seek MP4 Drive chính xác/ingest đa nền tảng |
| [G17/#30](https://github.com/cavoixanh638/kho-tri-thuc/pull/30) | Obsidian | 64 (54–72) | Live Preview Markdown, backlinks, Bases, offline | Rất tốt làm tham chiếu editor; không phải backend video/Drive |

## 3. Những lỗi thông tin G00 đã sửa, nguồn để tái kiểm

- **Capacities:** Bản G00 đầu từng sai khi ghi audio chưa phát hành. [Release 71](https://capacities.io/whats-new/release-71) có recording/transcription/summaries early access tháng 9; [Release 73](https://capacities.io/whats-new/release-73) đưa vào gói Pro tháng 11. [Media analysis](https://docs.capacities.io/reference/media-analysis) cần bật AI/analyze; [giới hạn media 100MB](https://docs.capacities.io/misc/media-upload) và [MP4 không native playback](https://docs.capacities.io/reference/basic-types/files). **Báo cáo G13 gốc đã đúng**, lỗi thuộc G00 bản trước.
- **Reflect Open:** [Repo chính thức](https://github.com/team-reflect/reflect-open) có Windows/Linux unsigned experimental và Android out of scope. [Blog ra mắt](https://reflect.app/blog/reflect-open) chỉ nói bản ban đầu, không dùng làm tình trạng mãi mãi.
- **Mem.ai:** [thông báo chính thức](https://get.mem.ai/blog/mem-is-shutting-down) công bố read-only 18/12/2026, đóng 15/01/2027.
- **Superpowered:** [trang tải](https://superpowered.me/download) không còn tải app mới; không kết luận mọi tài khoản cũ đã ngừng.
- **Google/Notebook:** [trang API](https://developers.google.com/notebook/docs) và [bài đổi tên](https://blog.google/innovation-and-ai/products/gemini-notebook/notebooklm-gemini-notebook/) nêu Preview/đổi tên; chưa chứng minh full raw video hoặc export/restore 100%.
- **Granola:** [thông tin bảo mật/retention](https://www.granola.ai/security) về không lưu âm thanh gốc, không thay chức năng replay.
- **Obsidian:** [Markdown edit/read](https://obsidian.md/help/edit-and-read), [Bases](https://obsidian.md/help/bases); phép xem tuyệt vời không thay được CaptureEvent/worker.
- **License:** [AFFiNE source](https://github.com/toeverything/AFFiNE) **không** cấp quyền sao chép tất cả thành phần vào sản phẩm mới mà không kiểm license theo package.

## 4. Quyết định triển khai để AI sử dụng

| Mã | Học từ | Hành động chỉ sau khi được giao |
| --- | --- | --- |
| KT-114 CORE | Cổng dữ liệu do dự án yêu cầu, không sản phẩm nào thay | QA corpus 10k/backup/Drive/ingestion với TEST/NOT_RUN rõ |
| KT-115 UX-P0 | G17, G09, G12, G01 | Editor Live Preview theo lựa chọn có thử; hiện chưa có |
| KT-116 UX-P0 | G16, G11, G05 | Citation → PDF page/video time có locator/asset thật |
| KT-117 CORE+UX-P0 | G02, G06, G09 | Android Share Target đã có; kiểm thật và tối ưu receipt |
| KT-118 UX-P1 | G01, G08, G12, G14 | Library Table/Card/Timeline cùng Item ID |
| KT-119 UX-P1 | G07, G13, G17 | Related/backlinks có nguồn & thẻ nguồn, không bịa link |
| KT-120 HOLD | G04, G07, G15 | AI gợi ý riêng, diff/accept; chờ quyền và ngân sách |
| KT-121 HOLD | G14, G13, G10 | Template/type fields tùy chọn; chờ yêu cầu cụ thể |

**Không thêm “task UX hoàn thành” vào CURRENT_STATE chỉ vì có tài liệu này.** Các task thuộc [INDEX](INDEX.md), code/tests/CI mới là căn cứ; G00 PR #47 và 17 nghiên cứu là nguồn để học, không phải bản copy code có thể chạy.
