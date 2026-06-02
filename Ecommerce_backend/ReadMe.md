# E-Commerce Backend — Complete Developer Guide

Dự án MVP e-commerce backend được xây dựng bằng **FastAPI + PostgreSQL + SQLAlchemy + Alembic + Redis**. 
Hướng dẫn này giải thích cấu trúc project, chức năng từng file, luồng hoạt động, và các bước triển khai.

---

## 📁 Project Structure & Chức Năng Từng File

### Root Level Files

```
ecommerce_backend/
├── requirements.txt          # Danh sách tất cả dependencies (FastAPI, SQLAlchemy, JWT, Redis)
├── .env                      # ⚠️ LOCAL ONLY - Cấu hình DATABASE_URL, SECRET_KEY, REDIS_URL (không commit)
├── .env.example              # Mẫu .env để devs copy
├── .gitignore                # Loại trừ __pycache__, .env, venv, logs từ Git
├── alembic.ini               # Cấu hình Alembic migrations
├── Dockerfile                # Build image Docker cho production
├── docker-compose.yml        # Khởi động PostgreSQL, Redis, App services
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
| **config.py** | Load settings từ `.env` bằng pydantic-settings (PROJECT_NAME, DATABASE_URL, REDIS_URL, SECRET_KEY) |
| **exceptions.py** | Định nghĩa BusinessRuleException & global handler trả về JSON {error_code, message} |
| **security.py** | ⚠️ CẦN IMPLEMENT — Hash password (bcrypt), tạo JWT token, verify token |

### app/db/ — Database Layer

| File | Chức Năng |
|------|----------|
| **database.py** | Tạo SQLAlchemy engine từ DATABASE_URL, SessionLocal session factory, get_db_session() dependency |
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
- `router.py` → `/login`, `/register`, `/me`

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
docker-compose up --build
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
services.py: create_access_token(user_id)
    ↓
Response: {"access_token": "jwt_token", "token_type": "bearer"}
    ↓
Client: GET /v1/products (header: Authorization: Bearer jwt_token)
    ↓
middleware/security: verify_token(jwt_token) → extract user_id
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
Copy-Item .env.example .env
```

**Linux/macOS:**
```bash
cp .env.example .env
```

Mở `.env` và điền giá trị:

```env
PROJECT_NAME="E-Commerce API"
DATABASE_URL="postgresql://user:pass@db:5432/ecommerce_db"
REDIS_URL="redis://redis:6379/0"
SECRET_KEY="your-secure-32-byte-secret-key"
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
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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

## 🛠️ Triển Khai Hàm để Hoàn Thành MVP

Các bước phát triển từng module. **Theo thứ tự:** Auth → Product → Order

### Module 1: AUTH — Đăng Ký & Đăng Nhập

#### 1.1 Implement app/core/security.py

```python
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

# Hash password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT Token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
```

#### 1.2 Implement app/modules/auth/models.py

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### 1.3 Implement app/modules/auth/schemas.py

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

#### 1.4 Implement app/modules/auth/services.py

```python
from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import BusinessRuleException

def register_user(db: Session, user_create: UserCreate) -> User:
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise BusinessRuleException(
            message="Email already registered",
            error_code="USER_ALREADY_EXISTS"
        )
    
    # Create new user
    user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        password_hash=hash_password(user_create.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise BusinessRuleException(
            message="Invalid email or password",
            error_code="INVALID_CREDENTIALS"
        )
    return user

def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessRuleException(
            message="User not found",
            error_code="USER_NOT_FOUND"
        )
    return user
```

#### 1.5 Implement app/modules/auth/router.py

```python
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.database import get_db_session
from app.modules.auth.schemas import UserCreate, LoginRequest, TokenResponse, UserResponse
from app.modules.auth.services import register_user, authenticate_user, get_user_by_id
from app.core.security import create_access_token, verify_token
from app.core.exceptions import BusinessRuleException
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db_session)):
    user = register_user(db, user_create)
    return user

@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, db: Session = Depends(get_db_session)):
    user = authenticate_user(db, login_request.email, login_request.password)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=7)
    )
    return {"access_token": access_token}

@router.get("/me", response_model=UserResponse)
def get_me(authorization: str = Header(...), db: Session = Depends(get_db_session)):
    # Extract token từ "Bearer <token>"
    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        raise BusinessRuleException("Invalid token", "INVALID_TOKEN")
    
    user = get_user_by_id(db, user_id)
    return user
```

#### 1.6 Include auth router trong app/main.py

```python
from app.modules.auth.router import router as auth_router

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # ... exception handler ...
    
    # Include auth router
    app.include_router(auth_router, prefix="/v1/auth", tags=["Auth"])
    
    return app
```

#### 1.7 Run Migration

```bash
alembic revision --autogenerate -m "create user table"
alembic upgrade head
```

#### 1.8 Test Auth Endpoints

```bash
# Register
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "full_name": "John Doe", "password": "pass123"}'

# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'

# Get Me
curl -X GET http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer <token-from-login>"
```

---

### Module 2: PRODUCT — Quản Lý Sản Phẩm

#### 2.1 Implement app/modules/product/models.py

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100))
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### 2.2 Implement app/modules/product/schemas.py

```python
from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock: int

class ProductUpdate(BaseModel):
    name: str = None
    description: str = None
    price: float = None
    stock: int = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    stock: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### 2.3 Implement app/modules/product/services.py

```python
from sqlalchemy.orm import Session
from app.modules.product.models import Product
from app.modules.product.schemas import ProductCreate, ProductUpdate
from app.core.exceptions import BusinessRuleException

def create_product(db: Session, product_create: ProductCreate) -> Product:
    product = Product(**product_create.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def get_products(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Product).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise BusinessRuleException("Product not found", "PRODUCT_NOT_FOUND")
    return product

def update_product(db: Session, product_id: int, product_update: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)
    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = get_product_by_id(db, product_id)
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}
```

#### 2.4 Implement app/modules/product/router.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db_session
from app.modules.product.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.modules.product.services import (
    create_product, get_products, get_product_by_id, 
    update_product, delete_product
)

router = APIRouter()

@router.post("", response_model=ProductResponse)
def create(product_create: ProductCreate, db: Session = Depends(get_db_session)):
    return create_product(db, product_create)

@router.get("", response_model=list[ProductResponse])
def list_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_session)):
    return get_products(db, skip, limit)

@router.get("/{product_id}", response_model=ProductResponse)
def get_one(product_id: int, db: Session = Depends(get_db_session)):
    return get_product_by_id(db, product_id)

@router.put("/{product_id}", response_model=ProductResponse)
def update_one(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db_session)):
    return update_product(db, product_id, product_update)

@router.delete("/{product_id}")
def delete_one(product_id: int, db: Session = Depends(get_db_session)):
    return delete_product(db, product_id)
```

#### 2.5 Include Product Router trong app/main.py

```python
from app.modules.product.router import router as product_router

def create_app() -> FastAPI:
    # ...
    app.include_router(product_router, prefix="/v1/products", tags=["Product"])
    return app
```

---

### Module 3: ORDER — Quản Lý Đơn Hàng

#### 3.1 Implement app/modules/order/models.py

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_price = Column(Float)
    status = Column(String(50), default="pending")  # pending, paid, completed, cancelled
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Giá tại thời điểm mua
```

#### 3.2 Implement app/modules/order/schemas.py

```python
from pydantic import BaseModel
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: list[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str
    items: list[OrderItemResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str
```

#### 3.3 Implement app/modules/order/services.py

```python
from sqlalchemy.orm import Session
from app.modules.order.models import Order, OrderItem
from app.modules.order.schemas import OrderCreate, OrderStatusUpdate
from app.modules.product.services import get_product_by_id
from app.core.exceptions import BusinessRuleException

def create_order(db: Session, user_id: int, order_create: OrderCreate) -> Order:
    total_price = 0
    
    # Validate & calculate total
    order_items_data = []
    for item in order_create.items:
        product = get_product_by_id(db, item.product_id)
        
        if product.stock < item.quantity:
            raise BusinessRuleException(
                f"Not enough stock for {product.name}",
                "INSUFFICIENT_STOCK"
            )
        
        total_price += product.price * item.quantity
        order_items_data.append((product, item.quantity))
    
    # Create order
    order = Order(user_id=user_id, total_price=total_price)
    db.add(order)
    db.flush()  # Get order.id
    
    # Create order items
    for product, quantity in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=product.price
        )
        db.add(order_item)
    
    db.commit()
    db.refresh(order)
    return order

def get_orders(db: Session, user_id: int):
    return db.query(Order).filter(Order.user_id == user_id).all()

def get_order_by_id(db: Session, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise BusinessRuleException("Order not found", "ORDER_NOT_FOUND")
    return order

def update_order_status(db: Session, order_id: int, status_update: OrderStatusUpdate) -> Order:
    order = get_order_by_id(db, order_id)
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    return order
```

#### 3.4 Implement app/modules/order/router.py

```python
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.database import get_db_session
from app.modules.order.schemas import OrderCreate, OrderResponse, OrderStatusUpdate
from app.modules.order.services import (
    create_order, get_orders, get_order_by_id, update_order_status
)
from app.core.security import verify_token
from app.core.exceptions import BusinessRuleException

router = APIRouter()

def get_current_user_id(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        raise BusinessRuleException("Invalid token", "INVALID_TOKEN")
    return user_id

@router.post("", response_model=OrderResponse)
def create(
    order_create: OrderCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    return create_order(db, user_id, order_create)

@router.get("", response_model=list[OrderResponse])
def list_orders(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    return get_orders(db, user_id)

@router.get("/{order_id}", response_model=OrderResponse)
def get_one(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    order = get_order_by_id(db, order_id)
    if order.user_id != user_id:
        raise BusinessRuleException("Not authorized", "UNAUTHORIZED")
    return order

@router.patch("/{order_id}", response_model=OrderResponse)
def update_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    order = get_order_by_id(db, order_id)
    if order.user_id != user_id:
        raise BusinessRuleException("Not authorized", "UNAUTHORIZED")
    return update_order_status(db, order_id, status_update)
```

#### 3.5 Include Order Router trong app/main.py

```python
from app.modules.order.router import router as order_router

def create_app() -> FastAPI:
    # ...
    app.include_router(order_router, prefix="/v1/orders", tags=["Order"])
    return app
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
  - [ ] `docker-compose up --build` chạy toàn bộ stack
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
  - [ ] Logging (tùy chọn)

---

## 🐳 Run with Docker Compose

```bash
docker-compose up --build
```

Các services sẽ start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI App (port 8000)

Test:
```bash
curl http://localhost:8000/v1/health
```

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
2. **DATABASE_URL**: Khi dùng docker-compose, hostname là `db` (tên service)
3. **.env**: Không commit. Giữ local
4. **Migrations**: Sau mỗi khi modify models, chạy `alembic revision --autogenerate`
5. **Token Authorization**: Format `Authorization: Bearer <token>`

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Kiểm tra `PYTHONPATH` hoặc activate venv |
| `DATABASE_URL not found` | Tạo `.env` từ `.env.example` |
| `alembic revision fails` | Import models trong `alembic/env.py` |
| `Connection refused` | Đảm bảo PostgreSQL/Redis running (docker-compose up) |
| `JWT verify fails` | Kiểm tra SECRET_KEY khớp, token chưa expire |

---

## 📚 References

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Alembic: https://alembic.sqlalchemy.org
- Pydantic: https://docs.pydantic.dev