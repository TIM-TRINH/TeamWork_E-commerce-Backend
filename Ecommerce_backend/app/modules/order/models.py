# app/modules/order/models.py
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class Order(Base):

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False) # FK to users
    total_amount = Column(Integer, nullable=False)
    status = Column(String, default="pending")

    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    product_id = Column(UUID(as_uuid=True), nullable=False) # FK to products
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")