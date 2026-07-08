from fastapi import APIRouter, Depends, status, Path, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.modules.product import schemas, services
from app.db.database import get_db_session

# DÙNG HÀNG THẬT: Phân quyền Admin từ module Auth
from app.modules.auth.dependencies import get_current_admin

router = APIRouter(
    prefix="/products",
    tags=["Product Catalog"],
    responses={404: {"description": "Product not found"}},
)

@router.post("/categories", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: schemas.CategoryCreate,
    db: Session = Depends(get_db_session),
    current_admin = Depends(get_current_admin)
):
    """Tạo danh mục mới (Chỉ Admin)."""
    return services.create_category(db=db, category_create=category_in)


@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db_session),
    current_admin = Depends(get_current_admin)  # BẮT BUỘC có token Admin
):
    """Tạo sản phẩm mới (Chỉ Admin)."""
    return services.create_product(db=db, product_create=product_in)


# LƯU Ý BẮT BUỘC: Route tĩnh (/search) PHẢI nằm TRƯỚC route có param động (/{product_id})
@router.get("/search", response_model=List[schemas.ProductResponse])
def search_products(
    params: schemas.ProductQueryParams = Depends(),
    db: Session = Depends(get_db_session)
):
    """
    Tìm kiếm sản phẩm theo từ khóa, danh mục, giá và sắp xếp.
    Public endpoint.
    """
    if not params.q:
        raise BusinessRuleException(
            message="Tham số q là bắt buộc cho tìm kiếm.",
            error_code="SEARCH_QUERY_REQUIRED",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return services.search_products(
        db=db,
        q=params.q,
        category_id=params.category_id,
        min_price=params.min_price,
        max_price=params.max_price,
        sort=params.sort,
        limit=params.limit,
    )


@router.get("/", response_model=List[schemas.ProductResponse])
def list_products(
    # BEST PRACTICE: Gom toàn bộ Query Params vào 1 model duy nhất
    params: schemas.ProductQueryParams = Depends(),
    db: Session = Depends(get_db_session)
):
    """Lấy danh sách sản phẩm với bộ lọc và Cursor Pagination. Public endpoint."""
    return services.get_products(
        db=db, 
        cursor=params.cursor, 
        limit=params.limit
    )


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(
    product_id: UUID = Path(..., description="UUID của sản phẩm"),
    db: Session = Depends(get_db_session)
):
    """Lấy thông tin chi tiết 1 sản phẩm. Public endpoint."""
    return services.get_product_by_id(db=db, product_id=product_id)


@router.patch("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_in: schemas.ProductUpdate,
    product_id: UUID = Path(...),
    db: Session = Depends(get_db_session),
    current_admin = Depends(get_current_admin) # Yêu cầu Admin
):
    """Cập nhật một phần thông tin sản phẩm (Chỉ Admin)."""
    return services.update_product(db=db, product_id=product_id, product_update=product_in)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID = Path(...),
    db: Session = Depends(get_db_session),
    current_admin = Depends(get_current_admin) # Yêu cầu Admin
):
    """Xóa sản phẩm (Chỉ Admin)."""
    services.delete_product(db=db, product_id=product_id)
    # LƯU Ý: HTTP 204 không được phép trả về bất kỳ dữ liệu (body) nào
    return None