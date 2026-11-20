# G00 — QUY TRÌNH NGHIÊN CỨU ĐỘC LẬP: ỨNG DỤNG GHI CHÚ/TRI THỨC (20/11/2026)

## Mục tiêu và phạm vi
Đánh giá công bằng từng ứng dụng để **chọn ý tưởng/tính năng áp dụng vào phần văn bản và quản lý nguồn của Kho Tri Thức**, không mặc định thay thế hay giữ hệ thống. Bối cảnh cần kiểm chứng ở GitHub: `cavoixanh638/kho-tri-thuc`, nhánh `main`, tài liệu `docs/MASTER_PLAN.md`, `docs/ARCHITECTURE_AND_DATA.md`, `docs/CAPTURE_AND_ORGANIZE.md`, `docs/CURRENT_STATE.md`. Ở ngày tạo bộ nhiệm vụ main có code React/Django/PostgreSQL, capture Event, nguồn media và Markdown, không còn là repo chỉ có kế hoạch. **Luồng phải tự fetch main mới nhất**; không kế thừa tuyên bố PASS từ tài liệu nếu thiếu log/evidence.

## 17 luồng nghiên cứu độc lập
Mỗi luồng chỉ đọc baseline Kho Tri Thức, tài liệu quy trình này và **hồ sơ sản phẩm được giao**. **Không đọc kết luận, bảng xếp hạng, bản nháp hoặc báo cáo của bất kỳ luồng nào khác trước khi nộp.** Không hỏi G00 về nhận định. Không chia sẻ số điểm/ranking giữa các luồng. Báo cáo độc lập được tổng hợp sau, không thay đổi sau khi xem ý kiến nhóm khác, trừ khi có nguồn mới và ghi lịch sử thay đổi.

## Nguồn và tính khách quan
1. Ưu tiên **tài liệu/hướng dẫn/release note chính thức cập nhật 2026**; tiếp đó GitHub source/license, marketplace docs, rồi thử thực tế. Nếu cần đối chiếu trải nghiệm người dùng, bổ sung một nguồn đánh giá độc lập có ngày.
2. Phân biệt **đã phát hành**, **beta**, **roadmap**, **tính năng trả phí**, **plugin bên thứ ba**, **cần tích hợp riêng**, **chưa tìm thấy bằng chứng**. Không coi marketing là test thực tế; không suy diễn từ tên gọi.
3. Ghi đường dẫn + ngày nguồn và ngày tự truy cập. Trạng thái năm 2026 có thể biến động, đặc biệt Mem, Coda/Superhuman Docs, Reflect Open, Gemini Notebook, Tana.
4. Không lưu token/dữ liệu cá nhân người dùng, không dùng tài khoản hoặc dịch vụ trả phí nếu chưa được cấp quyền; nếu chưa được thử UI trực tiếp, đánh dấu `NOT_RUN`.

## Bộ tình huống chung (K01–K12)
- K01: Gõ ngay 1 ghi chú tiếng Việt, nhận receipt và thời điểm.
- K02: Gửi một URL video/web, tự lấy metadata và nội dung khi có.
- K03: Gửi link trùng sau 1 ngày; phân biệt capture-event mới với retry request.
- K04: Ghi chú chứa Markdown, bảng, liên kết; lưu lại không mất dữ liệu/Unicode.
- K05: Tự phát hiện nhóm cùng chủ đề và **gán vào nhóm đã có**; không chỉ đề xuất.
- K06: Đưa các mục khác nhau có liên quan lên cạnh bài, backlinks/mối quan hệ.
- K07: Lưu PDF/audio/video và nhảy đúng trang/timestamp được dẫn chứng.
- K08: Cùng một bài thuộc nhiều lĩnh vực, nhiều chế độ xem (tree/table/card/timeline).
- K09: Chạy được trên Android + Windows; offline/online và xử lý xung đột.
- K10: Mở API, xuất/nhập markdown và assets, bản backup và thoát nhà cung cấp.
- K11: AI phân biệt nguồn trích, gợi ý vs sửa nội dung người dùng, quyền/chi phí.
- K12: Quy mô trên 10.000 items và hàng trăm GB video qua Drive/remote storage (kiểm evidence, không suy là hỗ trợ).

Mỗi ca ghi `NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED`; có trích dẫn và phạm vi plan/platform.

## Thang điểm dùng chung (không ép thành một kết luận)
Chấm các lĩnh vực: capture + ingestion 20 điểm, organization + recall 20, text editor + reading 15, provenance/related/timestamps 15, Android/Windows/offline 10, portability/backup 10, integration/cost/maintainability 10. Mỗi trụ ghi **điểm + lý do + độ tin cậy**. Đưa `UNVERIFIED` là thiếu bằng chứng, **không tự chấm 0**; cho khoảng điểm nếu dữ liệu thiếu. Tách hai kết quả: **mức phù hợp nếu thay thế toàn hệ thống** và **tiềm năng học/tái sử dụng từng tính năng**.

## Đầu ra bắt buộc của mỗi luồng
1. Executive summary trung tính (tối đa 200 từ).
2. Bằng chứng chính thức về tính năng, năm, nền tảng, API, export, offline, source, retention, giá/license.
3. K01–K12 ma trận kèm đường dẫn nguồn; bất kỳ điểm chưa thử phải nói NOT_RUN.
4. Ưu điểm và nhược điểm **so với code thực đang có** của Kho Tri Thức, không so với bản kế hoạch cũ.
5. 3–6 ý tưởng đáng mượn, mức độ triển khai (S/M/L), phụ thuộc và rủi ro; không tự thêm công nghệ nặng.
6. Đề xuất **Không áp dụng / Tham khảo UX / Thử PoC / Tích hợp thư viện / Thay toàn bộ**, có điều kiện đảo chiều quyết định và trường hợp phản chứng.
7. Bằng chứng/nguồn tối thiểu 5 URL, ít nhất 3 từ nguồn chính thức nếu có; ghi ngày truy cập. Không bịa test/pricing.

## Điều phối code/PR
Không sửa code ứng dụng, MASTER_PLAN, roadmap hoặc CURRENT_STATE ở đợt nghiên cứu. Mỗi luồng chỉ sở hữu **một file** `docs/research/notes-apps-20261120/reports/Gxx-<slug>.md` trên branch `research/notes-20261120-gxx`; nếu có GitHub write access thì commit + PR nhưng **KHÔNG tự merge**. Nếu không có quyền GitHub, trả báo cáo đầy đủ ở chat riêng và ghi rõ chưa commit. G00 chỉ tổng hợp sau khi có các kết quả độc lập, review tính nhất quán và kiểm chứng claim từ nguồn; không thay kết luận độc lập bằng điểm tùy hứng.
