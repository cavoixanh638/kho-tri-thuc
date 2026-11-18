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
