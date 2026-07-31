# E-Commerce Backend — Complete Developer Guide

Dự án MVP e-commerce backend được xây dựng bằng **FastAPI + PostgreSQL + SQLAlchemy + Alembic + Redis**. 
Hướng dẫn này giải thích cấu trúc project, chức năng từng file, luồng hoạt động, và các bước triển khai.

---

## 📁 Project Structure & Chức Năng Từng File

### Root Level Files

```
ecommerce_backend/
├── requirements.txt          # Runtime dependencies cho production
├── requirements-dev.txt      # Test và hot-reload dependencies
├── .env                      # ⚠️ LOCAL ONLY - Cấu hình DATABASE_URL, SECRET_KEY, REDIS_URL (không commit)
├── env.example               # Mẫu .env để devs copy
├── .gitignore                # Loại trừ __pycache__, .env, venv, logs từ Git
├── .dockerignore             # Giảm build context và loại trừ secrets
├── alembic.ini               # Cấu hình Alembic migrations
├── Dockerfile                # Multi-stage, non-root production image
├── docker-compose.yml        # Production base: DB, Redis, migration, app
├── docker-compose.override.yml # Bind mount và hot reload cho development
├── ReadMe.md                 # Hướng dẫn này
```

### app/main.py — Entry Point (Chính)
**Chức năng:** Khởi tạo FastAPI app, đăng ký routers, cấu hình exception handlers, health check.

```python
# Luồng chạy:
1. create_app() — tạo FastAPI instance
2. Đăng ký global exception handler cho BusinessRuleException
3. Include routers từ auth, product, order modules
4. /v1/health endpoint — kiểm tra trạng thái server
```

### app/core/ — Cấu Hình & Bảo Mật

| File | Chức Năng |
|------|----------|
| **config.py** | Load và validate logging, token, pool, Redis settings từ environment |
| **exceptions.py** | Định nghĩa BusinessRuleException & global handler trả về JSON {error_code, message} |
| **logging.py** | Cấu hình stdout logging; DEBUG ở development, INFO ở production |
| **security.py** | Hash password bằng bcrypt và JWT có `token_type`, `jti`, `session_id` |

### app/db/ — Database Layer

| File | Chức Năng |
|------|----------|
| **database.py** | Tạo QueuePool hoặc NullPool từ environment và cung cấp DB session |
| **redis.py** | Redis client dùng cho refresh-token sessions và readiness |
| **base_class.py** | Khai báo SQLAlchemy declarative_base() — cha mẹ của tất cả models |

### app/modules/ — Feature Modules (Chứa Logic Business)

Mỗi module (auth, product, order) có cấu trúc **4 file**:

```
modules/auth/
├── models.py       # SQLAlchemy ORM models (User, Role, Permission)
├── schemas.py      # Pydantic request/response schemas (LoginRequest, TokenResponse, UserResponse)
├── services.py     # Business logic (authenticate, register, hash_password, create_token)
├── router.py       # FastAPI endpoints (@router.post, @router.get, etc.)
```

**Luồng xử lý HTTP request:**
```
Client Request 
    → router.py (nhận request)
    → schemas.py (validate input)
    → services.py (logic, database query)
    → models.py (interact với DB)
    → response (trả JSON)
```

**Module Auth:**
- `models.py` → `User` model (id, email, password_hash, created_at)
- `schemas.py` → `LoginRequest`, `TokenResponse`, `UserResponse`
- `services.py` → `authenticate_user()`, `create_access_token()`, `hash_password()`
- `router.py` → `/login`, `/register`, `/refresh-token`, `/logout`, `/me`

**Module Product:**
- `models.py` → `Product` model (id, name, price, description, category, stock)
- `schemas.py` → `ProductCreate`, `ProductResponse`, `ProductUpdate`
- `services.py` → `create_product()`, `get_products()`, `get_product_by_id()`, `update_product()`, `delete_product()`
- `router.py` → `/products` (CRUD endpoints)

**Module Order:**
- `models.py` → `Order`, `OrderItem` models
- `schemas.py` → `OrderCreate`, `OrderResponse`
- `services.py` → `create_order()`, `get_orders()`, `get_order_by_id()`, `update_order_status()`
- `router.py` → `/orders` (CRUD endpoints)

### alembic/ — Database Migrations

| File | Chức Năng |
|------|----------|
| **env.py** | Cấu hình Alembic để lấy DATABASE_URL từ `.env`, auto-detect model changes |
| **versions/** | Thư mục chứa migration scripts (tự động tạo khi chạy `alembic revision --autogenerate`) |

---

## 🔄 Luồng Hoạt Động (Architecture Flow)

### 1️⃣ Khởi Động Server

```
docker compose up --build
    ↓
PostgreSQL (port 5432) + Redis (port 6379) ready
    ↓
FastAPI app (port 8000) loads settings từ .env
    ↓
SQLAlchemy engine connects tới DB
    ↓
Routers registered (auth, product, order)
    ↓
GET /v1/health → {"status": "ok"}
```

### 2️⃣ User Authentication Flow

```
Client: POST /v1/auth/login {email, password}
    ↓
router.py: validate email & password (schemas)
    ↓
services.py: hash_password(password) compare với DB
    ↓
services.py: tạo Redis refresh session và cặp access/refresh token
    ↓
Response: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
    ↓
Client: GET /v1/products (header: Authorization: Bearer jwt_token)
    ↓
dependencies.py: decode token với expected_type="access" → extract user_id
    ↓
Endpoint executes as authenticated user
```

### 3️⃣ Product CRUD Flow

```
Client: POST /v1/products {name, price, description}
    ↓
router.py: validate schema (ProductCreate)
    ↓
services.py: call models to insert DB
    ↓
models.py: create Product row in PostgreSQL
    ↓
Response: ProductResponse {id, name, price, created_at}
```

### 4️⃣ Database Migration Flow

```
Dev: Define new model (e.g., Order class)
    ↓
Dev: alembic revision --autogenerate -m "add order model"
    ↓
Alembic detects changes in models.py
    ↓
Auto-generates SQL migration in alembic/versions/
    ↓
Dev: alembic upgrade head
    ↓
SQL migration runs → PostgreSQL schema updated
```

---

## 🚀 Quick Start — Clone & Setup

### Step 1: Clone Repository

**Windows (PowerShell):**
```powershell
git clone <repo-url> ecommerce_backend
cd ecommerce_backend
```

**Linux/macOS:**
```bash
git clone <repo-url> ecommerce_backend
cd ecommerce_backend
```

### Step 2: Tạo File .env từ Mẫu

**Windows:**
```powershell
Copy-Item env.example .env
```

**Linux/macOS:**
```bash
cp env.example .env
```

Mở `.env` và điền giá trị:

```env
PROJECT_NAME="E-Commerce API"
DEBUG=False
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
POSTGRES_USER=user
POSTGRES_PASSWORD=change-me
POSTGRES_DB=ecommerce_db
DATABASE_URL="postgresql://user:change-me@db:5432/ecommerce_db"
REDIS_URL="redis://redis:6379/0"
SECRET_KEY="your-secure-32-byte-secret-key"
DB_POOL_MODE=queue
```

**Cách sinh SECRET_KEY an toàn:**

Python (all OS):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy output vào `SECRET_KEY=...`

### Step 3: Install Docker (Recommended for API module tests)

**Windows / macOS:**
1. Tải Docker Desktop từ: https://www.docker.com/products/docker-desktop
2. Cài đặt và khởi động Docker Desktop
3. Chờ icon Docker báo trạng thái ready


**Kiểm tra Docker đã chạy:**
```bash
docker ps
```

### Step 4: Setup Virtual Environment & Dependencies

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements-dev.txt
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Step 4: Database Migrations (Alembic)

Cần làm sau khi models được define (xem bước dưới):

```bash
# Tạo initial migration
alembic revision --autogenerate -m "init models"

# Apply migrations
alembic upgrade head
```

### Step 5: Chạy Server Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Kiểm tra:
```
GET http://localhost:8000/v1/health
```

Response:
```json
{"status": "ok", "message": "Service is running perfectly."}
```

---

## ✅ Checklist Hoàn Thành MVP

- [ ] **Auth Module Complete**
  - [ ] User model, schemas, services, router
  - [ ] hash_password(), verify_password(), create_access_token() implement
  - [ ] /v1/auth/register endpoint hoạt động
  - [ ] /v1/auth/login endpoint trả token
  - [ ] /v1/auth/me endpoint verify token
  - [ ] Migration: `alembic upgrade head` chạy thành công

- [ ] **Product Module Complete**
  - [ ] Product model, schemas, services, router
  - [ ] CRUD endpoints: POST, GET, GET/{id}, PUT/{id}, DELETE/{id}
  - [ ] Migration tạo products table

- [ ] **Order Module Complete**
  - [ ] Order, OrderItem models, schemas, services, router
  - [ ] POST /v1/orders tạo đơn hàng
  - [ ] GET /v1/orders lấy danh sách
  - [ ] GET /v1/orders/{id} lấy chi tiết
  - [ ] PATCH /v1/orders/{id} update trạng thái
  - [ ] Validation: check stock product trước khi tạo order
  - [ ] Authorization: user chỉ xem được order của mình
  - [ ] Migration tạo orders, order_items tables

- [ ] **Docker & Deployment**
  - [ ] docker-compose.yml có app service
  - [ ] DATABASE_URL, REDIS_URL, SECRET_KEY cấu hình đúng
    - [ ] `docker compose up --build` chạy toàn bộ stack
  - [ ] Kiểm tra health: `GET /v1/health`

- [ ] **Database & Migrations**
  - [ ] Tất cả models import vào `alembic/env.py`
  - [ ] `alembic revision --autogenerate -m "init"` tạo migration
  - [ ] `alembic upgrade head` apply thành công
  - [ ] All tables created: users, products, orders, order_items

- [ ] **Testing Endpoints**
  - [ ] Register user & login lấy token
  - [ ] Create product
  - [ ] Create order với valid product & quantity
  - [ ] Get order & verify order owner

- [ ] **Code Quality**
  - [ ] Không commit `.env`
  - [ ] Xử lý lỗi dùng BusinessRuleException
  - [ ] Tất cả endpoints return JSON spec (error_code, message)
    - [ ] Logging không chứa password, token hoặc secret

---

## 🐳 Run with Docker Compose

Development (tự động dùng `docker-compose.override.yml`):

```bash
docker compose up --build
```

Production base, không bind mount hoặc reload:

```bash
docker compose -f docker-compose.yml up --build
```

PostgreSQL và Redis chỉ publish host ports trong development override. Service
`migrate` chạy `alembic upgrade head` một lần; app chỉ start sau khi DB/Redis
healthy và migration hoàn tất.

Test:
```bash
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/ready
```

`/v1/health` là liveness không phụ thuộc external services. `/v1/ready` kiểm tra
PostgreSQL và Redis, trả HTTP 503 khi app chưa sẵn sàng nhận traffic.

### Logging

- `DEBUG=True`: log level DEBUG.
- `DEBUG=False`: log level INFO; warning/error vẫn được ghi.
- Password, JWT và secret không được ghi log ở bất kỳ level nào.

### Refresh-token security

Mỗi lần login tạo một Redis session riêng cho thiết bị. Refresh token có
`session_id` và `jti`, chỉ dùng một lần. Rotation được thực hiện atomically bằng
Redis Lua script. Nếu token cũ bị replay, toàn bộ session đó bị revoke; session
trên thiết bị khác không bị ảnh hưởng. `/v1/auth/logout` revoke session hiện tại.
Redis session state không persist trong Compose: Redis restart sẽ fail closed bằng
cách buộc tất cả thiết bị đăng nhập lại, tránh khôi phục một JTI cũ đã bị rotate.

### Database pool

Container dùng `DB_POOL_MODE=queue`; serverless hoặc external pooler có thể chọn
`DB_POOL_MODE=null`. Connection ceiling phải được tính trước khi scale:

```text
replicas × workers × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

Giữ một phần PostgreSQL connection budget cho migration, admin và service khác.

---

## 📝 Useful Commands

```bash
# Activate venv
.\venv\Scripts\Activate  # Windows
source venv/bin/activate  # Linux/macOS

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic current
alembic history
```

---

## ⚠️ Important Notes

1. **SECRET_KEY**: KHÔNG để rỗng. Sinh bằng `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. **DATABASE_URL**: Khi dùng Docker Compose, hostname là `db`; chạy app trực tiếp thì dùng `localhost`
3. **.env**: Không commit. Giữ local
4. **Migrations**: Sau mỗi khi modify models, chạy `alembic revision --autogenerate`
5. **Token Authorization**: Chỉ access token dùng format `Authorization: Bearer <token>`
6. **Image digests**: Docker images được pin digest; cập nhật digest định kỳ cùng security patches

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Kiểm tra `PYTHONPATH` hoặc activate venv |
| `DATABASE_URL not found` | Tạo `.env` từ `env.example` |
| `alembic revision fails` | Import models trong `alembic/env.py` |
| `Connection refused` | Đảm bảo PostgreSQL/Redis running (`docker compose up`) |
| `JWT verify fails` | Kiểm tra SECRET_KEY khớp, token chưa expire |
| Refresh trả `AUTH_STORE_UNAVAILABLE` | Kiểm tra Redis health và `REDIS_URL` |

---

## 📚 References

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Alembic: https://alembic.sqlalchemy.org
- Pydantic: https://docs.pydantic.dev