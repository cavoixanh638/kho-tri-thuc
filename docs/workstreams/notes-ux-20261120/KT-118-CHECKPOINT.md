# KT-118 — nhiều cách xem cùng Item

Branch `codex/kt-118-library-views`, baseline `7044b4a`. Root là writer duy nhất.
Code đã viết: Danh sách/Bảng/Thẻ/Theo ngày dùng cùng một server page, URL lưu
scope/filter/offset/mode. Chuyển mode không fetch lại, không sort 10k ở browser;
timeline dùng saved_at giờ Việt Nam và ghi rõ phạm vi trang hiện tại.

Kiểm đã chạy: `node --test tests/kt118-library.test.mjs` 4 PASS, gồm đi hết 200
page/10k fixture ở cả bốn mode, raw objects không đổi, stable tied timestamp,
URL/filters/offset, XSS, mode không tạo fetch. `npm test` 19 PASS; build PASS.
KT114 [PR48](https://github.com/cavoixanh638/kho-tri-thuc/pull/48) có DB test10k,
138 nhánh/221 paged reads/restore15collection; backend ở cùng baseline không đổi.
Không đánh đồng frontend fixture với browser đọc trực tiếp toàn DB.

Browser cô lập `tests/kt118-browser.html` tại loopback8118: đã nhìn Bảng 1920x1080,
Thẻ 390x844. Đang chỉnh mục lục mobile thu gọn và type column. Chưa chốt browser
PASS cho bản cuối; Android thiết bị thật NOT_RUN. Không đụng runtime production.
Style achromatic-ledger seed236088050, giữ palette/type/shell hiện hữu, không thêm
brand/font/dependency; chữ và đường dẫn sách là dấu nhận diện.

Tiếp: kiểm lại browser390/768/1920 và keyboard/paging; tests sau CSS/markup mới;
commit/push và PR không merge. Shared runner/api/styles/CURRENT_STATE không đổi.
