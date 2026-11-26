# Chạy scaffold Kho Tri Thức

Các lệnh Docker Compose bên dưới đã chạy trên runner Ubuntu 24.04 của GitHub Actions. [Kết quả kiểm thử](https://github.com/cavoixanh638/kho-tri-thuc/actions/runs/44320811635)

## Khởi động

Dùng một bản checkout từ GitHub trong môi trường có Docker và Docker Compose v2. Từ thư mục gốc repo, tạo `.env` từ mẫu nếu chưa có file này. Mẫu chứa giá trị dành riêng cho môi trường phát triển.

```bash
cp .env.example .env
docker compose config --quiet
docker compose up --detach --build --wait --wait-timeout 120
```

Compose khởi động PostgreSQL và chạy migration trước khi mở API. Worker khởi động sau khi API qua health check. PostgreSQL dùng volume riêng và chỉ được truy cập trong mạng Compose.

- Mở [Kho Tri Thức](http://127.0.0.1:5173) để thấy trạng thái kết nối của UI.
- [API health](http://127.0.0.1:8000/api/v1/health) trả `{"status":"ready"}` khi kết nối được PostgreSQL. Cùng endpoint qua [proxy frontend](http://127.0.0.1:5173/api/v1/health) dùng để kiểm tra đường đi từ web.
- Có thể đổi `API_PORT` và `WEB_PORT` trong `.env` khi cổng host đang bận.

## Trọng số BGE cho tìm kiếm gần nghĩa

BGE chạy trên CPU và giữ trọng số tại máy chạy ứng dụng. Lần chuẩn bị đầu cần
khoảng 588 MB tải xuống. Lệnh chuẩn bị kiểm SHA-256 và dùng lại các tệp đã hợp lệ.
Ứng dụng dùng xếp hạng dự phòng khi chưa có model.

Windows: `python tools/windows/launch.py setup` tự chuẩn bị model tại
`%LOCALAPPDATA%/KhoTriThuc/models/bge-reranker-v2-m3`. Nếu bước tải thất bại,
setup tiếp tục. Để chạy lại riêng bước này, mở `apps/backend` và chạy:

```powershell
& "$env:LOCALAPPDATA/KhoTriThuc/venv/Scripts/python.exe" -m search.prepare_bge
```

Docker Compose: chạy lệnh một lần trước khi khởi động stack để đưa trọng số vào
volume `search-models`. Thư mục mặc định trong container là
`/var/lib/kho-tri-thuc/models/bge-reranker-v2-m3`.

```bash
docker compose run --rm --no-deps --build api python -m search.prepare_bge
```

Có thể thêm `--from-dir <đường-dẫn-model>` để xác minh và sao chép bộ trọng số
đã có mà không cần mạng. Nếu chạy trong Docker, đường dẫn nguồn phải được gắn vào
container. Biến `SEARCH_BGE_MODEL_DIR` chỉ tới thư mục chứa `config.json`,
`tokenizer.json` và thư mục con `onnx`. Trong Compose, chọn đường dẫn trong
volume model để giữ tệp giữa các lần tạo container. Đặt biến thành chuỗi rỗng
để tắt BGE. Tiến trình tìm kiếm chỉ đọc tệp local.

## Kiểm tra

```bash
docker compose exec -T api python manage.py check --database default
docker compose exec -T api python manage.py makemigrations --check --dry-run
docker compose exec -T api python manage.py migrate --check
docker compose exec -T api python manage.py test
docker compose exec -T worker python manage.py run_worker --check
```

Image frontend chạy `npm ci` và `npm run build`. Job CI còn rollback và áp lại migration `sessions` trên database dùng một lần. [Workflow kiểm thử](../../.github/workflows/smoke.yml)

## Dọn môi trường dùng một lần

Lệnh dưới dừng các container và **xóa volume PostgreSQL của stack này**. Chỉ chạy khi dữ liệu thử có thể bỏ.

```bash
docker compose down --volumes
```
