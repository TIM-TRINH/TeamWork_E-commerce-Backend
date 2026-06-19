import pytest
import httpx
from typing import Dict, Any, Optional
import uuid

# Cấu hình Base URL của server đang chạy
BASE_URL = "http://localhost:8000/v1"

@pytest.mark.asyncio
async def test_80_20_ecommerce_flow() -> None:
    """
    Integration test covers the 80/20 critical path for a customer:
    1. Register a new user.
    2. Login with the new user to get a JWT token.
    3. (Assumes a product exists) Fetch an existing product.
    4. Use the token to create a new order for that product.
    5. Verify the order was created successfully.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        
        # --- STEP 1: REGISTER & LOGIN ---
        # Sử dụng email ngẫu nhiên để mỗi lần chạy test là một user mới
        unique_email = f"customer_{uuid.uuid4().hex[:8]}@team1.com"
        user_payload: Dict[str, Any] = {
            "email": unique_email,
            "name": "Test Customer",
            "password": "StrongPassword123!"
        }
        # Đăng ký
        register_response = await client.post("/auth/register", json=user_payload)
        # User có thể đã tồn tại nếu chạy test lại, chấp nhận 201 hoặc 400 (đã tồn tại)
        # Một test tốt hơn sẽ dọn dẹp DB trước mỗi lần chạy
        assert register_response.status_code in [201, 400]
        
        # Đăng nhập lấy Token
        login_payload = {
            "email": user_payload["email"],
            "password": user_payload["password"]
        }
        login_response = await client.post("/auth/login", json=login_payload)
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token: str = login_response.json()["access_token"]
        headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}

        # --- STEP 2: GET A PRODUCT ---
        # Giả định rằng có ít nhất một sản phẩm trong DB để test.
        # Trong một môi trường test thực tế, chúng ta sẽ tạo sản phẩm này trong một bước setup.
        list_prod_response = await client.get("/products", params={"limit": 1})
        assert list_prod_response.status_code == 200, "Could not fetch products."
        products = list_prod_response.json()
        
        if not products:
            pytest.skip("Skipping order test: No products found in the database to order.")

        product_id: str = products[0]["product_id"]

        # --- STEP 3: CHECKOUT / ORDER ---
        # Lưu ý: Schema của bạn dùng UUID, nên product_id phải là string UUID
        order_payload: Dict[str, Any] = {
            "items": [
                {"product_id": product_id, "quantity": 1}
            ]
            # Các trường như shipping_address, payment_method không có trong OrderCreate schema hiện tại
        }
        order_response = await client.post("/orders", json=order_payload, headers=headers)
        
        # Đảm bảo đơn hàng tạo thành công
        assert order_response.status_code == 201, f"Order creation failed: {order_response.text}"
        
        order_data = order_response.json()
        print(f"\nOrder created successfully: {order_data}")
        
        assert "order_id" in order_data
        assert order_data["status"] == "pending"
        assert len(order_data["items"]) == 1
        assert order_data["items"][0]["product_id"] == product_id
        assert order_data["items"][0]["quantity"] == 1