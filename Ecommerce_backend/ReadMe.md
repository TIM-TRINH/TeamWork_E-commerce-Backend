E-Commerce Backend — Developer Onboarding

Tài liệu này hướng dẫn nhanh cho team dev cách clone project, cấu hình môi trường, và chạy ứng dụng để bắt đầu phát triển các modules (auth, product, order).

## 1) Clone repository

```powershell
git clone <repo-url> ecommerce_backend
cd ecommerce_backend
```

## 2) Tạo file `.env` từ mẫu

Repository giữ một file mẫu `.env.example`. Mỗi dev cần tạo file `.env` cục bộ (không commit) và điền giá trị thực tế.

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Sau đó mở `.env` và sửa các biến:
- `DATABASE_URL` — chuỗi kết nối tới PostgreSQL
- `REDIS_URL` — URL Redis
- `SECRET_KEY` — KHÔNG để rỗng (xem phần dưới để sinh key an toàn)

Ví dụ khi chạy cùng Docker Compose (host của DB/Redis là tên service trong compose):

```env
PROJECT_NAME="E-Commerce API"
DATABASE_URL="postgresql://user:pass@db:5432/ecommerce_db"
REDIS_URL="redis://redis:6379/0"
SECRET_KEY="<replace-with-secure-value>"
```

> Lưu ý: `.env` đã được thêm vào `.gitignore` — tuyệt đối không commit file này.

## 3) Tạo `SECRET_KEY` an toàn

`SECRET_KEY` dùng để ký JWT, cookie, HMAC,... Phải là giá trị ngẫu nhiên, tối thiểu 32 bytes.

PowerShell (Windows):

```powershell
# Sinh Base64 32 bytes
$r = New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($r); [System.Convert]::ToBase64String($r)
Write-Output $r
```

Python (bất kỳ OS):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy giá trị sinh ra và đặt vào `.env`:

```
SECRET_KEY="(giá trị bạn vừa tạo)"
```

## 4) Thiết lập môi trường ảo và cài dependencies

Windows (PowerShell):

```powershell
# Tạo và kích hoạt venv
python -m venv venv
.\venv\Scripts\Activate

# Cài dependencies
pip install -r requirements.txt
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5) Chạy ứng dụng local (development)

Sau khi cài xong và tạo `.env`, chạy server bằng uvicorn:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt hoặc curl để kiểm tra health:

```
GET http://localhost:8000/v1/health
```

## 6) Chạy toàn bộ stack bằng Docker Compose (tùy chọn)

File `docker-compose.yml` hiện chỉ khai báo `db` và `redis`. Để chạy app trong compose, bạn có 2 lựa chọn:

- Thêm service `app` vào `docker-compose.yml` (cách nhanh cho dev). Ví dụ:

```yaml
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ecommerce_app
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
    command: >
      sh -c "pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
```

> Lưu ý: khi chạy trong compose, `DATABASE_URL` và `REDIS_URL` trong `.env` nên dùng hostname `db` và `redis` tương ứng.

Ví dụ `.env` cho compose:

```
DATABASE_URL="postgresql://user:pass@db:5432/ecommerce_db"
REDIS_URL="redis://redis:6379/0"
```

Nếu bạn muốn, mình có thể tạo `Dockerfile` mẫu — báo để mình scaffold.

Chạy compose:

```bash
docker compose up --build
# hoặc
docker-compose up --build
```

## 7) Migrations (Alembic)

Trước khi chạy migration, đảm bảo `alembic` cấu hình để lấy `DATABASE_URL` từ environment (hoặc `.env`). `alembic.ini`/`env.py` cần được kiểm tra/cập nhật.

Tạo migration và áp dụng:

```bash
# tạo revision tự động (sau khi đã define models)
alembic revision --autogenerate -m "init models"
alembic upgrade head
```

Nếu gặp lỗi, kiểm tra `alembic/env.py` để đảm bảo nó đọc `os.environ['DATABASE_URL']` hoặc tương đương.

## 8) Include routers

File `app/main.py` đang có `health` endpoint nhưng chưa include routers cho các modules. Khi triển khai endpoints:

```python
from app.modules.auth.router import router as auth_router
app.include_router(auth_router, prefix='/v1/auth', tags=['Auth'])
```

Mỗi module (auth, product, order) có cấu trúc tách biệt:
- `models.py` — SQLAlchemy models
- `schemas.py` — Pydantic schemas
- `services.py` — business logic
- `router.py` — FastAPI routes

Luồng chuẩn: router -> schemas validation -> services -> crud/models -> db

## 9) Kiểm tra nhanh sau khi khởi động

- Health: `GET /v1/health` trả status ok
- Nếu có auth router, test đăng ký / đăng nhập

## 10) Quy tắc commit / bảo mật

- KHÔNG commit `.env` hoặc secrets. `.gitignore` đã loại trừ `.env`.
- Các secret cho production phải được lưu trên Secret Manager (AWS/Azure/GCP) hoặc biến môi trường CI/CD.

## 11) Checklist nhanh cho team lead trước khi release dev-ready

- [ ] Mọi dev đã tạo `.env` và có `SECRET_KEY` hợp lệ
- [ ] Thêm `app` service vào `docker-compose.yml` (hoặc hướng dẫn chạy app local)
- [ ] Include tất cả routers cần thiết trong `app/main.py`
- [ ] Alembic `env.py`/`alembic.ini` cấu hình, migration init và `alembic upgrade head` chạy thành công
- [ ] README có hướng dẫn chạy, migrate và test
- [ ] Thêm tests cơ bản cho auth/product/order
- [ ] Kiểm tra không commit secrets và .gitignore hợp lệ

## 12) Nếu cần trợ giúp

Nếu bạn muốn, mình có thể:
- Tạo `Dockerfile` mẫu và chèn `app` service vào `docker-compose.yml`.
- Cập nhật `app/main.py` để include router `auth` làm ví dụ.
- Tạo `alembic/env.py` mẫu để lấy `DATABASE_URL` từ env.

Ghi chú ngắn: bắt đầu bằng việc yêu cầu mọi dev tạo `.env` và chạy `uvicorn` local; bước tiếp theo là chuẩn hóa Docker Compose và migrations.

---

Hãy thông báo nếu muốn mình scaffold (Dockerfile / include router / alembic env) — mình sẽ tạo PR mẫu.
chạy lệnh: .\venv\Scripts\activate mỗi khi test project trên môi trường ảo tránh chạy trên máy.