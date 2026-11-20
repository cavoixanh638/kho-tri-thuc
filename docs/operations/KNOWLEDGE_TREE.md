# Cây thư viện, bài tri thức và nguồn minh họa

Hướng dẫn cho tính năng KT-113 theo mã nguồn hiện hành. Kết quả triển khai và
nghiệm thu nằm ở [CURRENT_STATE.md](../CURRENT_STATE.md); tài liệu này không
thay báo cáo chạy thật.

## Đọc và tổ chức tri thức

Một **bài tri thức** có một nội dung và một định danh. Mục lục là cách tìm đến
bài: có thể xếp cùng bài vào nhiều nhánh mà không sao chép văn bản hay video.
Cây mục lục nằm trong PostgreSQL, không buộc tạo lại cây thư mục trên Drive.

Trong **Thư viện**, chọn **Thêm kho con** để tạo một nhánh gốc. Chọn nhánh rồi
dùng **Thêm nhánh con** để chia nhỏ; **Đổi tên / chuyển nhánh** cho đổi tên,
loại và nhánh cha. Các loại Kho con, Lĩnh vực, Bộ sách, Sách, Chương, Nhánh
giúp nhận biết mục lục, không ép mỗi kho phải có cùng số tầng. Chẳng hạn:

```text
Công nghệ và vận hành
└─ Cơ sở dữ liệu
   └─ PostgreSQL
      └─ Vận hành PostgreSQL
         └─ Sao lưu và khôi phục
```

Đây có thể là bộ sưu tập do người dùng biên soạn; nhãn “Sách” không tự khẳng
định đó là một đầu sách đã xuất bản. Nên tạo nhánh khi đã có nội dung cần xếp,
giữ tên rõ nghĩa và chia nhỏ dần khi một nhánh trở nên khó tìm.

- Chọn một nhánh để đọc cả các bài thuộc nhánh con. Số bài ở nhánh cha đếm
  theo bài duy nhất, kể cả khi bài được xếp ở nhiều nhánh bên dưới.
- **Chưa xếp mục lục** tìm các bài chưa thuộc nhánh đang hoạt động. Bài vẫn
  có thể có Project hoặc Tag; đó là các nhóm bổ sung ngoài cây mục lục.
- Trong bài, chọn **Nhóm của mục → Chỉnh nhóm**, tìm theo đường dẫn đầy đủ
  rồi chọn một hoặc nhiều nhánh. Nhóm người dùng chốt được cố định, không để
  phân loại tự động thay thế.
- Không thể chuyển nhánh vào chính nó hoặc nhánh con của nó. Mã hiện tại
  giới hạn 5.000 nút và 64 tầng cho mỗi chủ sở hữu; đây là giới hạn bảo vệ,
  không phải cấu trúc khuyến khích dùng đủ.

## Văn bản chính và nguồn đi kèm

**Gửi vào kho → Văn bản / Markdown** dùng cho bài tự viết hoặc biên soạn.
Trong bài, **Chỉnh sửa** sửa phần văn bản chính; xem thêm
[Đọc và viết Markdown](TEXT_KNOWLEDGE.md).

**Gắn nguồn / video minh họa vào bài** nhận URL cho chính bài đang mở. Ứng
dụng lưu lượt tiếp nhận rồi xử lý nền để lấy văn bản khả dụng. Nguồn mới
không tạo một bài rời khác và không ghi đè note đã biên soạn. Retry cùng
request key giữ cùng lượt tiếp nhận; một lần gửi thực sự mới vẫn có lịch sử.

Phần **Tri thức** ưu tiên văn bản người dùng. Khi chưa có bài biên soạn,
ứng dụng đọc text trích hiện hành, ưu tiên phụ đề/transcript nếu có. Khi đã
có bài biên soạn, text nguồn vẫn đọc được trong **Các phần trích và bằng
chứng nguồn**. Các bản trích có processor, phiên bản và thông tin truy nguyên;
chúng không trở thành chỉnh sửa của người dùng.

Video, ảnh và tài liệu nằm trong phần có thể mở **Video, media và tài liệu
minh họa** phía sau phần đọc. **Xem minh họa từ nguồn** mở phần này; **Mở
tệp** truy cập bản gốc đã xác minh trên Drive. Thao tác này chưa phải cam kết
tua trình phát đến đúng mốc transcript.

Nguồn web được trích phần nội dung khả dụng; trang cần đăng nhập, trang chỉ
dựng bằng script hoặc nguồn không truy cập được có thể chưa cho text. Trạng
thái lỗi/thiếu text được giữ rõ ràng. Lưu URL hoặc video thành công không tự
đồng nghĩa đã có kiến thức từ nội dung đó.

Các bộ đếm lượt xem, thích, cảm xúc, chia sẻ, bình luận bị loại khỏi metadata
nguồn; các phần tiêu đề/mô tả chỉ chứa bộ đếm cũng được làm sạch. Nội dung bài
người dùng và lịch sử đầu vào nguyên gốc không bị viết lại để làm sạch nguồn.

## Chép lời video trên Windows

ASR là tùy chọn, chỉ bật khi cấu hình `LOCAL_ASR_MODEL_DIR` trỏ đến model đã
chuẩn bị. Worker dùng faster-whisper với model `base`, CPU/int8, chạy suy luận
offline trong tiến trình con. Lần chuẩn bị tải model công khai; suy luận không
tự tải model và không gửi video tới dịch vụ AI bên ngoài.

Bản chép lời giữ ngôn ngữ nguồn được nhận diện. Video tiếng Anh có transcript
tiếng Anh; chưa tự dịch hoặc biến thành bài kiến thức đã biên tập. Nhãn **Bản
chép lời tự động trên Windows** yêu cầu đối chiếu video trước khi sử dụng.
Người dùng có thể biên soạn nội dung chính sau khi kiểm lại; transcript và
nguồn vẫn được giữ kèm theo.

Phạm vi hiện tại:

| Thành phần | Giới hạn |
| --- | --- |
| Đầu vào | Asset video/audio gốc đã xác minh trên Drive, tối đa 128 MiB |
| Thời lượng | Có audio và thời lượng xác định, lớn hơn 0 và không quá 600 giây |
| Suy luận | CPU 4 luồng, một worker model; timeout tiến trình con 420 giây |
| Kết quả | Tối đa 1.000 đoạn, 100.000 ký tự; mốc thời gian không vượt clip |
| Phiên bản | Job theo hash bản gốc và phiên bản processor; retry không tạo bản gốc mới |

Model sai checksum, clip vượt giới hạn, thiếu audio, lời nói không nhận được
hoặc lỗi xử lý sẽ không tạo nội dung giả. File gốc và bài đã biên soạn vẫn
được giữ. Khi model đã bật, upload đã xác minh có thể tạo tác vụ transcript;
luồng **Thử xử lý lại** hỗ trợ cả media đã lưu từ trước.

Người vận hành dùng Python của ứng dụng để cài phụ thuộc tùy chọn và chuẩn bị
model; chạy từ root source đã checkout đúng phiên bản:

```powershell
$ktRuntime = Join-Path $env:LOCALAPPDATA 'KhoTriThuc'
$ktPython = Join-Path $ktRuntime 'venv\Scripts\python.exe'
$ktModel = Join-Path $ktRuntime 'models\whisper-base'
& $ktPython -m pip install -r apps/backend/processing/requirements-asr.txt
& $ktPython tools/prepare_local_asr.py $ktModel
```

`prepare_local_asr.py` tải model tại revision đã pin và kiểm SHA-256 của
`model.bin`, tạo `kt-model.json`. Cấu hình môi trường API/worker
`LOCAL_ASR_MODEL_DIR` bằng đường dẫn `$ktModel`, rồi restart theo
[hướng dẫn Windows](WINDOWS_SETUP.md). Không dùng model trong Git hoặc thư
mục đồng bộ source. Để tắt ASR cho tác vụ mới, để cấu hình này rỗng; văn bản
đã trích và file gốc vẫn còn.

## Sắp xếp các bài khởi đầu

Lệnh riêng `organize_starter_knowledge` nhận diện bốn bài công khai đã nhập
từ `docs/knowledge/` và Reel Golf ban đầu, xếp vào cây mẫu mà không sao chép
Item. Đây không phải bộ tự phân loại mọi nội dung cá nhân.

Trong môi trường backend đã cấu hình đúng database, chạy từ `apps/backend`:

```powershell
python manage.py organize_starter_knowledge --owner admin
python manage.py organize_starter_knowledge --owner admin --apply
```

Lệnh đầu chỉ preview. `--apply` tạo/tái sử dụng nhánh, cố định quan hệ các bài
được nhận diện và làm sạch metadata nguồn, tiêu đề/mô tả có bộ đếm trong kho
của chủ sở hữu đó. Note, URL gốc, file gốc và giờ nhận được giữ. Không dùng
lệnh này thay thao tác phân nhóm tùy ý cho bài mới.

## Xuất và khôi phục

**Bản xuất tri thức** vẫn bật riêng theo từng bài, lưu vào
`Kho Tri Thuc/ChatGPT_Index` trên Drive. Bản xuất có đường dẫn nhóm, văn bản,
nguồn và provenance; đổi cây hoặc text tạo phiên bản mới trên cùng tệp quản
lý. ChatGPT chỉ đọc được những bản xuất đã đồng bộ và connector được phép
truy cập; cây PostgreSQL không tự trở thành cây Drive.

Backup manifest v3 bổ sung loại/thứ tự nhánh, giữ cha-con và quan hệ bài.
Tool chấp nhận manifest v1/v2; kết quả restore thật của từng phiên bản phải
đọc trong báo cáo nghiệm thu, không suy từ tương thích schema. Xem
[Backup/restore](BACKUP_RESTORE.md).

GitHub giữ source, migration, test, tài liệu và kết quả đã khử thông tin
riêng. Model weights/cache, transcript riêng, media, OAuth, cấu hình runtime
và database dump nằm ngoài Git. File gốc/bản xuất/backup thuộc các vị trí
Drive và bản sao Windows quy định trong
[REPOSITORY_LAYOUT.md](../REPOSITORY_LAYOUT.md).
