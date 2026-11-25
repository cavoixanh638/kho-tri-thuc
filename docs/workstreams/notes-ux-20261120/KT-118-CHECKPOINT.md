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

Code/Tested SHA `a20072e46a4d4111c7355bb1007b66ab760732d2`. Đọc lại 201 page API
từ DB KT114 sau thử capture: 10.001 Item, bốn mode cùng thứ tự/tập ID, 0 dòng
trùng; objects note/source/asset không bị đổi. `KT118_DB_FIXTURE` trỏ JSON ngoài
Git dùng cho new test; chạy thêm lần không có env dùng 10k fixture tied timestamp.
`tests/kt118-export-db.py` có guard DB prefix/loopback62224/read-only transaction.
Không sửa server pagination/sort hoặc tải 10k bài vào browser ứng dụng.

Browser cô lập `tests/kt118-browser.html` tại loopback8118: Bảng/Thẻ/Danh sách/
Theo ngày, chuyển page giữ mode và ID đúng, không tràn trang ở 1920x1080,
768x1024, 390x844. Mục lục tablet/mobile mặc định gọn; bảng cuộn trong frame.
Ảnh fixture đính kèm cùng thư mục, [báo cáo](KT-118-EVIDENCE.json).
Android thiết bị thật và browser đọc toàn bộ 201 page DB là NOT_RUN; phép so tập
DB chạy bằng renderer/DOM test. Không đụng runtime production.
Style achromatic-ledger seed236088050, giữ palette/type/shell hiện hữu, không thêm
brand/font/dependency; chữ và đường dẫn sách là dấu nhận diện.

Tái chạy: `npm test`, `node --test tests/kt118-library.test.mjs`, `npm run build`;
muốn lặp DB, chạy export script với `--database` và `--output` ở ngoài Git rồi
đặt env `KT118_DB_FIXTURE` đến file đó. Không gọi jsdom là thiết bị thật.
Tiếp: push/tạo PR, theo dõi CI, **không merge/deploy**. Shared runner/api/styles/
CURRENT_STATE không đổi; revert PR trả về list mặc định, không thay schema.
