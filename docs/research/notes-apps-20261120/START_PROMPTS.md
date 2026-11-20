# 17 PROMPT KHỞI CHẠY — KHẢO SÁT ĐỘC LẬP ỨNG DỤNG GHI CHÚ/TRI THỨC

**Ngày:** 20/11/2026  
**Dự án:** [Kho Tri Thức](https://github.com/cavoixanh638/kho-tri-thuc)  
**Trạng thái:** prompt giao việc sẵn dùng; chưa hàm ý 17 luồng đã chạy hoặc đã có báo cáo.

## Hướng dẫn

Mở **17 cuộc trò chuyện ChatGPT riêng biệt**. Với mỗi cuộc, sao chép **nguyên văn một khối prompt** tương ứng ở dưới. Không đưa các báo cáo của luồng khác vào cuộc trò chuyện mới. Các luồng có thể làm đồng thời. Sau khi nộp, G00 kiểm chứng nguồn rồi mới tổng hợp quyết định; không tự merge hoặc sửa ứng dụng.

**Mỗi luồng chỉ nghiên cứu đúng một sản phẩm / một họ sản phẩm liền mạch được nêu đích danh, không khảo sát thay cho luồng khác.** Chi tiết: [INDEX.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/INDEX.md) · [G00-PROTOCOL.md](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md).

## G01 — Notion

[Hồ sơ chi tiết G01](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G01-NOTION.md)

```text
Bạn là luồng G01 — chuyên gia nghiên cứu độc lập Notion cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Notion. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G01-NOTION.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: block editor, cơ sở dữ liệu, relations/rollups, các kiểu view, Web Clipper, AI agent và offline; kiểm tra giới hạn gói và khả năng xuất toàn bộ dữ liệu.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G01-NOTION.md trên nhánh research/notes-20261120-g01, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G02 — Google Keep

[Hồ sơ chi tiết G02](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G02-GOOGLE-KEEP.md)

```text
Bạn là luồng G02 — chuyên gia nghiên cứu độc lập Google Keep cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Google Keep. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G02-GOOGLE-KEEP.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: quy trình ghi chú thật nhanh trên Android, share-sheet, ghi âm, ảnh/OCR, labels, pin, reminders, offline và khả năng trích xuất/đồng bộ qua API.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G02-GOOGLE-KEEP.md trên nhánh research/notes-20261120-g02, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G03 — Lark Docs/Wiki/Base

[Hồ sơ chi tiết G03](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G03-LARK.md)

```text
Bạn là luồng G03 — chuyên gia nghiên cứu độc lập Lark Docs/Wiki/Base cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Lark Docs/Wiki/Base. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G03-LARK.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: Doc/Wiki/Base liên kết, AI phân loại và tự điền trường, tự động hóa workflow, cấu trúc phân cấp, quản trị quyền và tính di động của dữ liệu.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G03-LARK.md trên nhánh research/notes-20261120-g03, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G04 — Evernote

[Hồ sơ chi tiết G04](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G04-EVERNOTE.md)

```text
Bạn là luồng G04 — chuyên gia nghiên cứu độc lập Evernote cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Evernote. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G04-EVERNOTE.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: Web Clipper, tìm kiếm ngữ nghĩa, OCR/scan PDF, AI biên tập, ghi chú đa phương tiện, xuất ENEX/Markdown, chi phí và hạn chế lưu trữ.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G04-EVERNOTE.md trên nhánh research/notes-20261120-g04, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G05 — Microsoft OneNote

[Hồ sơ chi tiết G05](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G05-ONENOTE.md)

```text
Bạn là luồng G05 — chuyên gia nghiên cứu độc lập Microsoft OneNote cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Microsoft OneNote. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G05-ONENOTE.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: canvas soạn thảo tự do, sections/pages, ghi âm gắn nội dung theo thời gian, handwriting, Copilot Notebooks (phân biệt sản phẩm), Android/Windows và backup/export.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G05-ONENOTE.md trên nhánh research/notes-20261120-g05, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G06 — Apple Notes

[Hồ sơ chi tiết G06](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G06-APPLE-NOTES.md)

```text
Bạn là luồng G06 — chuyên gia nghiên cứu độc lập Apple Notes cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Apple Notes. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G06-APPLE-NOTES.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: Quick Notes, share/capture, tag/Smart Folders, scan/OCR, ghi âm và phiên âm, liên kết note, dùng từ Windows/Android và thoát hệ sinh thái Apple.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G06-APPLE-NOTES.md trên nhánh research/notes-20261120-g06, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G07 — Mem.ai

[Hồ sơ chi tiết G07](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G07-MEM-AI.md)

```text
Bạn là luồng G07 — chuyên gia nghiên cứu độc lập Mem.ai cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Mem.ai. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G07-MEM-AI.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: trạng thái dịch vụ và thông báo thay đổi/ngừng cung cấp, Heads Up/related notes, AI tự tổ chức, xuất dữ liệu, bài học chống vendor lock-in và khả năng học UX dù dịch vụ không còn thích hợp tích hợp.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G07-MEM-AI.md trên nhánh research/notes-20261120-g07, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G08 — Coda / Superhuman Docs

[Hồ sơ chi tiết G08](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G08-CODA.md)

```text
Bạn là luồng G08 — chuyên gia nghiên cứu độc lập Coda / Superhuman Docs cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Coda / Superhuman Docs. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G08-CODA.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: thay đổi tên/thương hiệu, connected tables, formulas, Packs, buttons, automations, docs AI, các quyền/bản giá và dữ liệu có thể xuất.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G08-CODA.md trên nhánh research/notes-20261120-g08, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G09 — Reflect Classic / Reflect Open

[Hồ sơ chi tiết G09](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G09-REFLECT.md)

```text
Bạn là luồng G09 — chuyên gia nghiên cứu độc lập Reflect Classic / Reflect Open cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Reflect Classic / Reflect Open. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G09-REFLECT.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: tình trạng bản Classic và Open, local-first Markdown, backlinks, daily notes, web capture, FTS/CLI, bảo mật/giấy phép mã nguồn và hỗ trợ Android/Windows.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G09-REFLECT.md trên nhánh research/notes-20261120-g09, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G10 — Superpowered AI Notetaker

[Hồ sơ chi tiết G10](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G10-SUPERPOWERED.md)

```text
Bạn là luồng G10 — chuyên gia nghiên cứu độc lập Superpowered AI Notetaker cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Superpowered AI Notetaker. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G10-SUPERPOWERED.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: ghi chú cuộc họp không bot, live transcription, action items, template, nguồn audio, bảo mật/retention, hỗ trợ hệ điều hành và cách khai thác ý tưởng cho media có timestamp.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G10-SUPERPOWERED.md trên nhánh research/notes-20261120-g10, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G11 — Gemini Notebook / NotebookLM

[Hồ sơ chi tiết G11](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G11-GEMINI-NOTEBOOK.md)

```text
Bạn là luồng G11 — chuyên gia nghiên cứu độc lập Gemini Notebook / NotebookLM cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Gemini Notebook / NotebookLM. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G11-GEMINI-NOTEBOOK.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: truy vấn có trích nguồn, phân tích YouTube/PDF/web/audio, source anchoring, notebook, kết nối Google Drive, giới hạn nguồn/tài khoản và khả năng API/export.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G11-GEMINI-NOTEBOOK.md trên nhánh research/notes-20261120-g11, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G12 — AFFiNE

[Hồ sơ chi tiết G12](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G12-AFFINE.md)

```text
Bạn là luồng G12 — chuyên gia nghiên cứu độc lập AFFiNE cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm AFFiNE. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G12-AFFINE.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: local-first/self-host, block editor/BlockSuite, canvas/whiteboard, database views, sync trên đa thiết bị, quyền riêng tư, giấy phép CE/EE và khả năng tái sử dụng thư viện thay vì fork ứng dụng.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G12-AFFINE.md trên nhánh research/notes-20261120-g12, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G13 — Capacities

[Hồ sơ chi tiết G13](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G13-CAPACITIES.md)

```text
Bạn là luồng G13 — chuyên gia nghiên cứu độc lập Capacities cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Capacities. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G13-CAPACITIES.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: object-based notes, object types, relations, backlinks, highlights, AI media analysis, API/export, chi phí AI và trải nghiệm trên Android/Windows.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G13-CAPACITIES.md trên nhánh research/notes-20261120-g13, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G14 — Tana Outliner

[Hồ sơ chi tiết G14](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G14-TANA.md)

```text
Bạn là luồng G14 — chuyên gia nghiên cứu độc lập Tana Outliner cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Tana Outliner. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G14-TANA.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: supertags, typed nodes, live searches, AI autofill, quy trình capture/voice, quan hệ tri thức, export và chi phí/lock-in; không nhầm với tana.inc.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G14-TANA.md trên nhánh research/notes-20261120-g14, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G15 — Granola

[Hồ sơ chi tiết G15](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G15-GRANOLA.md)

```text
Bạn là luồng G15 — chuyên gia nghiên cứu độc lập Granola cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Granola. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G15-GRANOLA.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: ghi chú cuộc họp với người dùng biên tập, transcription, tóm tắt có dẫn chứng, quyền riêng tư/retention, Android/Windows, API/MCP và bài học trích timestamp.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G15-GRANOLA.md trên nhánh research/notes-20261120-g15, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G16 — Heptabase

[Hồ sơ chi tiết G16](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G16-HEPTABASE.md)

```text
Bạn là luồng G16 — chuyên gia nghiên cứu độc lập Heptabase cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Heptabase. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G16-HEPTABASE.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: source cards, PDF/YouTube/podcast, highlight về đúng đoạn/trang nguồn, whiteboard, phân cấp tri thức, mobile/Android, CLI/MCP, export và mức khó thực hiện.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G16-HEPTABASE.md trên nhánh research/notes-20261120-g16, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

## G17 — Obsidian

[Hồ sơ chi tiết G17](https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G17-OBSIDIAN.md)

```text
Bạn là luồng G17 — chuyên gia nghiên cứu độc lập Obsidian cho dự án “Kho Tri Thức” (repo riêng: https://github.com/cavoixanh638/kho-tri-thuc).

NHIỆM VỤ DUY NHẤT: nghiên cứu SÂU sản phẩm Obsidian. Không nghiên cứu các sản phẩm mà G01–G17 khác phụ trách, không đọc báo cáo/điểm số của luồng khác, không tham khảo G00-INITIAL-SOURCES.md trước khi nộp. Không mặc định sản phẩm tốt/xấu hoặc phải thay hệ thống hiện có.

ĐỌC TRƯỚC KHI LÀM:
- Quy trình + 12 tình huống kiểm tra + thang điểm thống nhất: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G00-PROTOCOL.md
- Hồ sơ nhiệm vụ riêng: https://github.com/cavoixanh638/kho-tri-thuc/blob/main/docs/research/notes-apps-20261120/G17-OBSIDIAN.md
- Repo main mới nhất, tối thiểu README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/MASTER_PLAN.md, docs/ARCHITECTURE_AND_DATA.md, docs/CAPTURE_AND_ORGANIZE.md; đối chiếu mã nguồn thực. Nếu tài liệu lịch sử nói chưa có code nhưng main đã có, lấy mã và bằng chứng nghiệm thu mới nhất làm chuẩn.

TRỌNG TÂM RIÊNG: Markdown local-first, Live Preview/editor, backlinks/graph, Bases, Canvas, plugin ecosystem, web clipper, mobile sync, bảo mật plugin và giới hạn khi dùng thay backend lưu video.

CÁCH NGHIÊN CỨU:
1) Chủ động dùng Web search, tài liệu chính thức, changelog mới nhất tới ngày đánh giá, GitHub chính thức và đánh giá thực tế có dẫn nguồn; kiểm tra bản phát hành/beta/roadmap, phân biệt chức năng native, extension, custom backend, chưa hỗ trợ/chưa có chứng cứ. Xác minh giá, giới hạn, quyền riêng tư, API/MCP, import/export, Android/Windows/offline, giấy phép, dữ liệu media/video.
2) Đánh giá đủ K01–K12 theo G00-PROTOCOL, mỗi ca có kết luận NATIVE / EXTENSION / CUSTOM_BACKEND / NOT_SUPPORTED / UNVERIFIED, dẫn link, phạm vi phiên bản/plan và bước tái kiểm thử. Không coi đọc metadata video là hiểu cả nội dung video; không nói đã thử trực tiếp khi chưa thử (NOT_RUN).
3) Đối chiếu với ứng dụng Kho Tri Thức hiện tại (capture event không mất lịch sử; PostgreSQL; Google Drive lưu file; phân nhóm/related items; ghi chú Markdown; tra cứu nguồn). Ghi rõ cái đã có, phần thua/kém, phần có thể học và rủi ro nếu thay thế.
4) Chấm 7 trụ theo thang 100 của G00, ghi độ tin cậy và khoảng điểm khi thiếu chứng cứ. TÁCH HAI KẾT LUẬN: (a) phù hợp để thay toàn hệ thống? (b) tính năng/UX nào đáng tham khảo, tích hợp hoặc làm PoC?
5) Đề xuất 3–6 tính năng áp dụng thiết thực, mức khó S/M/L, phụ thuộc, rủi ro, acceptance test đo được; không tự đổi framework/storage. Nếu đề xuất thay công nghệ phải có ít nhất 2–3 lựa chọn được so sánh và bằng chứng.

ĐẦU RA: báo cáo tiếng Việt có executive summary trung tính (<=200 từ), ma trận 12 ca, bảng 7 điểm, kết luận có phản chứng, ít nhất 5 URL trong đó >=3 nguồn chính thức nếu có; ghi ngày truy cập và phân biệt VERIFIED / INFERRED / NOT_RUN.

Chỉ tạo file báo cáo docs/research/notes-apps-20261120/reports/G17-OBSIDIAN.md trên nhánh research/notes-20261120-g17, commit/push và lập PR về main nếu có quyền GitHub; KHÔNG merge, KHÔNG sửa code, KHÔNG sửa báo cáo của luồng khác. Nếu không có quyền ghi GitHub, trả toàn bộ báo cáo ngay trong chat và ghi rõ chưa commit.

Thực hiện nghiên cứu và hoàn thành báo cáo ngay; không dừng ở lập kế hoạch.
```

