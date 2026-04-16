from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum


class Product(Base):
    __tablename__ = "products"
    sku = Column(String, primary_key=True, index=True)   # unique product code
    name = Column(String, nullable=False)
    # CHECK constraint added via migration
    stock = Column(Integer, nullable=False, default=0)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(
        String, unique=True, nullable=False, index=True)  # prevents duplicates
    status = Column(String, default="confirmed")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sku = Column(String, ForeignKey("products.sku"), nullable=False)
    quantity = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="items")
