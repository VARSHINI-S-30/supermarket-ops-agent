from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.database.db import Base


# =========================================================
# PRODUCT
# =========================================================

class Product(Base):

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    sku = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    unit = Column(
        String,
        nullable=False
    )

    cost_price = Column(
        Float,
        nullable=False
    )

    selling_price = Column(
        Float,
        nullable=False
    )

    mrp = Column(
        Float,
        nullable=False
    )

    quantity = Column(
        Float,
        nullable=False,
        default=0
    )

    reorder_level = Column(
        Float,
        nullable=False,
        default=0
    )

    gst_rate = Column(
        Float,
        nullable=False,
        default=0
    )

    hsn_code = Column(
        String,
        nullable=True
    )


# =========================================================
# CUSTOMER
# =========================================================

class Customer(Base):

    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False,
        index=True
    )

    phone = Column(
        String,
        unique=True,
        nullable=True,
        index=True
    )

    credit_balance = Column(
        Float,
        nullable=False,
        default=0
    )

    bills = relationship(
        "Bill",
        back_populates="customer"
    )


# =========================================================
# BILL
# =========================================================

class Bill(Base):

    __tablename__ = "bills"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="draft"
    )

    subtotal = Column(
        Float,
        nullable=False,
        default=0
    )

    gst_amount = Column(
        Float,
        nullable=False,
        default=0
    )

    total_amount = Column(
        Float,
        nullable=False,
        default=0
    )

    payment_mode = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    customer = relationship(
        "Customer",
        back_populates="bills"
    )

    items = relationship(
        "BillItem",
        back_populates="bill",
        cascade="all, delete-orphan"
    )


# =========================================================
# BILL ITEM
# =========================================================

class BillItem(Base):

    __tablename__ = "bill_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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

    quantity = Column(
        Float,
        nullable=False
    )

    unit_price = Column(
        Float,
        nullable=False
    )

    gst_rate = Column(
        Float,
        nullable=False
    )

    gst_amount = Column(
        Float,
        nullable=False
    )

    total_amount = Column(
        Float,
        nullable=False
    )

    bill = relationship(
        "Bill",
        back_populates="items"
    )

    product = relationship(
        "Product"
    )


# =========================================================
# TELEGRAM SESSION
# =========================================================

class TelegramSession(Base):

    __tablename__ = "telegram_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    telegram_user_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    conversation_json = Column(
        String,
        nullable=False,
        default="[]"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# =========================================================
# OWNER PREFERENCE
# =========================================================

class OwnerPreference(Base):

    __tablename__ = "owner_preferences"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    preference_key = Column(
        String,
        unique=True,
        nullable=False
    )

    preference_value = Column(
        String,
        nullable=False
    )