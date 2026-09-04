from sqlalchemy import Column, Integer, String, Float
from .db import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    sku = Column(String, unique=True, nullable=False)

    unit = Column(String, nullable=False)

    cost_price = Column(Float, nullable=False)

    selling_price = Column(Float, nullable=False)

    mrp = Column(Float, nullable=False)

    quantity = Column(Float, default=0)

    reorder_level = Column(Float, default=5)

    gst_rate = Column(Float, default=0)

    hsn_code = Column(String, nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    phone = Column(String, nullable=True)

    credit_balance = Column(Float, default=0)
    
class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True
    )

    status = Column(
        String,
        default="draft"
    )

    subtotal = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)

    payment_mode = Column(
        String,
        default="cash"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    customer = relationship("Customer")

    items = relationship(
        "BillItem",
        back_populates="bill",
        cascade="all, delete-orphan"
    )


class BillItem(Base):
    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, index=True)

    bill_id = Column(
        Integer,
        ForeignKey("bills.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(Float, nullable=False)

    unit_price = Column(Float, nullable=False)

    gst_rate = Column(Float, default=0)

    gst_amount = Column(Float, default=0)

    total_amount = Column(Float, default=0)

    bill = relationship(
        "Bill",
        back_populates="items"
    )

    product = relationship("Product")