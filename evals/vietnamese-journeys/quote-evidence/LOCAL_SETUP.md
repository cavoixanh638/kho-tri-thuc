# Chuẩn bị máy localhost

Chạy ở gốc checkout. Dùng Python 3.11 trở lên và môi trường ảo riêng. Chuẩn bị một PostgreSQL chuyên dùng cho QA, có `listen_addresses = '127.0.0.1'`. Ví dụ dùng cổng 55439 và tài khoản quản trị cục bộ `postgres`. Các lệnh tạo role và database trống trong instance QA đã khởi động. Nếu đã có database chuyên dùng với đúng tên và chưa có dữ liệu, cấu hình lại biến kết nối tương ứng rồi migrate. [PostgreSQL createuser](https://www.postgresql.org/docs/current/app-createuser.html), [PostgreSQL createdb](https://www.postgresql.org/docs/current/app-createdb.html).

## Windows PowerShell

```powershell
python -m venv .venv-quote-eval
$env:POSTGRES_DB = 'kt_eval_edge_pairs'
$env:POSTGRES_USER = 'kt_eval'
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_PORT = '55439'
$env:POSTGRES_PASSWORD = python -c 'import getpass; print(getpass.getpass("QA role password: "))'
$env:DJANGO_SECRET_KEY = python -c 'import secrets; print(secrets.token_urlsafe(32))'
$env:SEARCH_BGE_MODEL_DIR = Join-Path $HOME 'kt-eval-models/bge-reranker-v2-m3'
$py = (Resolve-Path '.\.venv-quote-eval\Scripts\python.exe').Path
& $py -m pip install -r apps/backend/requirements.txt
createuser -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U postgres --pwprompt kt_eval
createdb -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U postgres --owner kt_eval kt_eval_edge_pairs
& $py apps/backend/manage.py migrate --noinput
Push-Location apps/backend
try { & $py -m search.prepare_bge } finally { Pop-Location }
```

Nhập cùng mật khẩu QA ở lời nhắc `QA role password` và lời nhắc chọn mật khẩu role mới của `createuser`. Dùng `& $py` thay cho `python` trong các lệnh đo.

## Linux

```sh
python3 -m venv .venv-quote-eval
. .venv-quote-eval/bin/activate
python -m pip install -r apps/backend/requirements.txt
export POSTGRES_DB=kt_eval_edge_pairs POSTGRES_USER=kt_eval
export POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55439
POSTGRES_PASSWORD=$(python -c 'import getpass; print(getpass.getpass("QA role password: "))')
DJANGO_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
export POSTGRES_PASSWORD DJANGO_SECRET_KEY
export SEARCH_BGE_MODEL_DIR="$HOME/kt-eval-models/bge-reranker-v2-m3"
createuser -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres --pwprompt kt_eval
createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres --owner kt_eval kt_eval_edge_pairs
python apps/backend/manage.py migrate --noinput
(cd apps/backend && python -m search.prepare_bge)
```

Nhập cùng mật khẩu QA ở hai lời nhắc như trên. Runner đối chiếu cả địa chỉ server do PostgreSQL báo lại nên server phải nhận kết nối trực tiếp ở loopback.

## Reader dùng cho mode feature

Tải gói llama.cpp b12753 cho hệ điều hành và thiết bị được chọn. Phép đo Windows dùng bản `llama-b12753-bin-win-vulkan-x64.zip`, SHA-256 `fb92b740cefe4111ce45a7af9dd0db28618463d7e95d963ba0df047a32cf8027`. Tải Qwen3-4B-Instruct-2507 Q4_K_M ở bản GGUF có revision `4edb920b6f14e3b9284d4502a6485103d72cde05`, SHA-256 `8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc`. Xác minh bằng `Get-FileHash -Algorithm SHA256` trên Windows hoặc `sha256sum` trên Linux trước khi chạy. GGUF là bản lượng tử hoá của LM Studio Community từ model Qwen Apache-2.0. [llama.cpp b12753](https://github.com/ggml-org/llama.cpp/releases/tag/b12753), [Qwen gốc](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [GGUF đã ghim](https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF/blob/4edb920b6f14e3b9284d4502a6485103d72cde05/Qwen3-4B-Instruct-2507-Q4_K_M.gguf).

Windows PowerShell với Vulkan. Chạy `llama-server.exe --list-devices` để lấy tên thiết bị Vulkan. Dùng đường dẫn tới binary đã giải nén và model đã xác minh.

```powershell
& .\llama-server.exe --host 127.0.0.1 --port 19587 `
    --model .\Qwen3-4B-Instruct-2507-Q4_K_M.gguf --alias qwen3-4b-instruct-2507-q4_k_m `
    --ctx-size 8192 --parallel 1 --batch-size 512 --ubatch-size 256 `
    --threads 6 --threads-batch 6 --poll 0 --device Vulkan0 --gpu-layers all `
    --fit off --flash-attn auto --reasoning off --cache-ram 0 --no-webui
```

Linux với CPU.

```sh
./llama-server --host 127.0.0.1 --port 19587 \
  --model ./Qwen3-4B-Instruct-2507-Q4_K_M.gguf --alias qwen3-4b-instruct-2507-q4_k_m \
  --ctx-size 8192 --parallel 1 --batch-size 512 --ubatch-size 256 \
  --threads 6 --threads-batch 6 --poll 0 --device none --gpu-layers 0 \
  --fit off --flash-attn auto --reasoning off --cache-ram 0 --no-webui
```

Kiểm tra `http://127.0.0.1:19587/health` bằng `curl` từ cửa sổ khác. Khi nhận HTTP 200, có thể [chạy phép đo](REPLAY.md#chạy-thử-nghiệm). Tốc độ phụ thuộc vào thiết bị và cấu hình.

## Bật trong app để thử nút Tìm gần đúng

Trên Windows, đặt `$env:SEARCH_QUOTE_EVIDENCE_ENABLED = '1'` trong cửa sổ khởi động backend rồi khởi động lại app hoặc pilot QA. Ba biến `SEARCH_QUOTE_READER_URL`, `SEARCH_QUOTE_READER_MODEL` và `SEARCH_QUOTE_TIMEOUT_SECONDS` cho phép đổi địa chỉ loopback, tên mô hình và thời gian chờ. Mặc định lần lượt là `http://127.0.0.1:19587/v1/chat/completions`, `qwen3-4b-instruct-2507-q4_k_m` và 45 giây. Với Docker Compose, loopback là của container API. Khi quay về cấu hình cũ, đặt `SEARCH_QUOTE_EVIDENCE_ENABLED=0` rồi khởi động lại API.
