# G01 — Nghiên cứu độc lập: Notion
 
**Chuyên trách:** duy nhất Notion; không nghiên cứu/so sánh kết luận của các luồng khác trước khi nộp. **As of:** 20/11/2026. **Sản phẩm nguồn chính thức để bắt đầu:** https://www.notion.com/help/notion-agent

**Quy trình:** [G00-PROTOCOL.md](G00-PROTOCOL.md) là tiêu chí bắt buộc. Đối chiếu mã và thực trạng Kho Tri Thức (GitHub main tại thời điểm nghiên cứu), **không giả định ứng dụng hiện vẫn chỉ là kế hoạch**. Nếu không có kết nối tài khoản hoặc môi trường thử sản phẩm, đánh dấu NOT_RUN.

## Câu hỏi nghiên cứu riêng
Đánh giá database relations/views, agent actions, offline, block-editor, time stamps, native clipper; phân biệt AI capabilities theo plan và October 2026 release.

## Nhiệm vụ chi tiết
1. Mở website/docs/release note chính thức và, nếu có, GitHub chính thức; kiểm tra tính năng **đã phát hành/beta/planned**, hệ điều hành, gói trả phí, API/SDK/MCP, export, privacy/license và thời điểm cập nhật.
2. Đi qua **K01–K12** trong [G00-PROTOCOL.md](G00-PROTOCOL.md). Với mỗi ca ghi trạng thái NATIVE/EXTENSION/CUSTOM_BACKEND/NOT_SUPPORTED/UNVERIFIED, chứng cứ URL, các bước để tái thử, điểm thiếu chắc chắn.
3. Phân tích riêng: ưu điểm/nhược điểm về sử dụng cá nhân Việt Nam (Unicode/Android/Windows), thao tác gửi URL/video, metadata/sự kiện thời gian, AI và quan hệ tri thức; ưu tiên **nguồn gốc, không được đánh đồng trích text với hiểu nội dung toàn video**.
4. So sánh từng khả năng với code hiện hành của Kho Tri Thức, chỉ ra **đã có / cải thiện / chưa có / không phù hợp**. Không biến nghiên cứu thành đòi hỏi viết lại Django/PostgreSQL/Drive nếu chưa có bằng chứng.
5. Chấm 7 trụ theo rubric; tách **mức phù hợp thay toàn hệ thống** với **giá trị tham khảo tính năng**, có giả thuyết phản chứng và ít nhất 3 giới hạn/rủi ro.
6. Đề xuất 3–6 tính năng có thể áp dụng (ghi UX/technical/adapter và độ khó S/M/L), kèm test acceptance có thể đo, rủi ro lock-in/licensing.
7. Đầu ra **1 file báo cáo** `docs/research/notes-apps-20261120/reports/G01-NOTION.md` (file chưa tồn tại), source links, thời gian đánh giá, bằng chứng. Branch độc lập `research/notes-20261120-g01`, PR về main, **không merge**. Nếu không thể ghi GitHub, gửi đầy đủ văn bản trong chat riêng và xác nhận chưa commit.

**Kiểm soát khách quan:** Tự kiểm tra các giả định sai. Không đọc `G00-INITIAL-SOURCES.md`, không đọc báo cáo G01–G17 khác và không tham khảo bảng xếp hạng của G00 trước khi hoàn tất báo cáo. Kết luận có thể là "không phù hợp" nếu nguồn chứng minh như vậy.
