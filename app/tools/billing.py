from app.database.db import SessionLocal
from app.database.models import Bill, BillItem, Product, Customer


# ============================================================
# CREATE BILL
# ============================================================

def create_bill(customer_id=None):
    db = SessionLocal()

    try:
        # Check customer if provided
        if customer_id is not None:
            customer = (
                db.query(Customer)
                .filter(Customer.id == customer_id)
                .first()
            )

            if not customer:
                return {
                    "success": False,
                    "message": f"Customer with ID {customer_id} not found."
                }

        bill = Bill(
            customer_id=customer_id,
            status="draft",
            subtotal=0,
            gst_amount=0,
            total_amount=0,
            payment_mode="cash"
        )

        db.add(bill)
        db.commit()
        db.refresh(bill)

        return {
            "success": True,
            "message": "Bill created successfully.",
            "bill_id": bill.id,
            "status": bill.status,
            "customer_id": bill.customer_id,
            "subtotal": bill.subtotal,
            "gst_amount": bill.gst_amount,
            "total_amount": bill.total_amount
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error creating bill: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# ADD ITEM TO BILL
# ============================================================

def add_item_to_bill(bill_id, sku, quantity):
    db = SessionLocal()

    try:
        # Validate quantity
        if quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be greater than zero."
            }

        # Find bill
        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:
            return {
                "success": False,
                "message": f"Bill with ID {bill_id} not found."
            }

        # Bill must be editable
        if bill.status != "draft":
            return {
                "success": False,
                "message": "Only draft bills can be modified."
            }

        # Find product
        product = (
            db.query(Product)
            .filter(Product.sku == sku)
            .first()
        )

        if not product:
            return {
                "success": False,
                "message": f"Product with SKU '{sku}' not found."
            }

        # Check stock availability
        if quantity > product.quantity:
            return {
                "success": False,
                "message": (
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.quantity} {product.unit}"
                )
            }

        # Check if product already exists in this bill
        existing_item = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id,
                BillItem.product_id == product.id
            )
            .first()
        )

        if existing_item:
            new_quantity = existing_item.quantity + quantity

            if new_quantity > product.quantity:
                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.quantity} {product.unit}, "
                        f"already requested: {existing_item.quantity}"
                    )
                }

            existing_item.quantity = new_quantity

            item_subtotal = (
                existing_item.quantity *
                existing_item.unit_price
            )

            existing_item.gst_amount = (
                item_subtotal *
                existing_item.gst_rate /
                100
            )

            existing_item.total_amount = (
                item_subtotal +
                existing_item.gst_amount
            )

        else:
            item_subtotal = (
                quantity *
                product.selling_price
            )

            gst_amount = (
                item_subtotal *
                product.gst_rate /
                100
            )

            total_amount = (
                item_subtotal +
                gst_amount
            )

            bill_item = BillItem(
                bill_id=bill.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.selling_price,
                gst_rate=product.gst_rate,
                gst_amount=gst_amount,
                total_amount=total_amount
            )

            db.add(bill_item)

        # Flush changes
        db.flush()

        # Recalculate entire bill
        items = (
            db.query(BillItem)
            .filter(BillItem.bill_id == bill_id)
            .all()
        )

        subtotal = 0
        gst_amount = 0

        for item in items:

            item_subtotal = (
                item.quantity *
                item.unit_price
            )

            item.gst_amount = (
                item_subtotal *
                item.gst_rate /
                100
            )

            item.total_amount = (
                item_subtotal +
                item.gst_amount
            )

            subtotal += item_subtotal
            gst_amount += item.gst_amount

        bill.subtotal = subtotal
        bill.gst_amount = gst_amount
        bill.total_amount = subtotal + gst_amount

        db.commit()
        db.refresh(bill)

        return {
            "success": True,
            "message": "Item added to bill successfully.",
            "bill_id": bill.id,
            "product": product.name,
            "sku": product.sku,
            "quantity": quantity,
            "unit_price": product.selling_price,
            "gst_rate": product.gst_rate,
            "subtotal": bill.subtotal,
            "gst_amount": bill.gst_amount,
            "total_amount": bill.total_amount
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error adding item: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# FINALIZE BILL
# ============================================================

def finalize_bill(bill_id, payment_mode="cash"):
    db = SessionLocal()

    try:
        # Find bill
        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:
            return {
                "success": False,
                "message": f"Bill with ID {bill_id} not found."
            }

        # Prevent finalizing an already finalized bill
        if bill.status == "finalized":
            return {
                "success": False,
                "message": "Bill is already finalized."
            }

        # Only draft bills can be finalized
        if bill.status != "draft":
            return {
                "success": False,
                "message": "Only draft bills can be finalized."
            }

        # Validate payment mode
        allowed_payment_modes = {
            "cash",
            "upi",
            "card",
            "credit"
        }

        payment_mode = payment_mode.lower()

        if payment_mode not in allowed_payment_modes:
            return {
                "success": False,
                "message": (
                    f"Invalid payment mode. Allowed: "
                    f"{', '.join(sorted(allowed_payment_modes))}"
                )
            }

        # ====================================================
        # CREDIT / KHATA VALIDATION
        # ====================================================

        if payment_mode == "credit":

            # Credit bill must have a customer
            if bill.customer_id is None:
                return {
                    "success": False,
                    "message": (
                        "A customer is required for "
                        "credit/khata bills."
                    )
                }

            # Find customer
            customer = (
                db.query(Customer)
                .filter(Customer.id == bill.customer_id)
                .first()
            )

            if not customer:
                return {
                    "success": False,
                    "message": (
                        f"Customer with ID "
                        f"{bill.customer_id} not found."
                    )
                }

        # ====================================================
        # GET BILL ITEMS
        # ====================================================

        items = (
            db.query(BillItem)
            .filter(BillItem.bill_id == bill_id)
            .all()
        )

        if not items:
            return {
                "success": False,
                "message": "Cannot finalize an empty bill."
            }

        # ====================================================
        # RE-CHECK STOCK BEFORE DEDUCTION
        # ====================================================

        for item in items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            if not product:
                return {
                    "success": False,
                    "message": (
                        f"Product for bill item {item.id} "
                        f"was not found."
                    )
                }

            if item.quantity > product.quantity:
                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for {product.name}. "
                        f"Required: {item.quantity} {product.unit}, "
                        f"Available: {product.quantity} {product.unit}"
                    )
                }

        # ====================================================
        # DEDUCT STOCK
        # ====================================================

        for item in items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            product.quantity -= item.quantity

        # ====================================================
        # UPDATE CUSTOMER KHATA BALANCE
        # ====================================================

        if payment_mode == "credit":

            customer.credit_balance += bill.total_amount

        # ====================================================
        # UPDATE BILL
        # ====================================================

        bill.status = "finalized"
        bill.payment_mode = payment_mode

        db.commit()
        db.refresh(bill)

        return {
            "success": True,
            "message": "Bill finalized successfully.",
            "bill_id": bill.id,
            "status": bill.status,
            "payment_mode": bill.payment_mode,
            "customer_id": bill.customer_id,
            "credit_added": (
                bill.total_amount
                if payment_mode == "credit"
                else 0
            ),
            "subtotal": bill.subtotal,
            "gst_amount": bill.gst_amount,
            "total_amount": bill.total_amount
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error finalizing bill: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# UPDATE BILL ITEM
# ============================================================

def update_bill_item(bill_id, sku, quantity):
    db = SessionLocal()

    try:
        # Validate quantity
        if quantity < 0:
            return {
                "success": False,
                "message": "Quantity cannot be negative."
            }

        # Find bill
        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:
            return {
                "success": False,
                "message": f"Bill with ID {bill_id} not found."
            }

        # Only draft bills can be edited
        if bill.status != "draft":
            return {
                "success": False,
                "message": "Only draft bills can be edited."
            }

        # Find product
        product = (
            db.query(Product)
            .filter(Product.sku == sku)
            .first()
        )

        if not product:
            return {
                "success": False,
                "message": f"Product with SKU '{sku}' not found."
            }

        # Find bill item
        bill_item = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id,
                BillItem.product_id == product.id
            )
            .first()
        )

        if not bill_item:
            return {
                "success": False,
                "message": (
                    f"{product.name} is not present in this bill."
                )
            }

        # ====================================================
        # QUANTITY = 0 MEANS REMOVE ITEM
        # ====================================================

        if quantity == 0:

            db.delete(bill_item)

        else:

            # Check stock
            if quantity > product.quantity:
                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.quantity} {product.unit}"
                    )
                }

            bill_item.quantity = quantity

        # ====================================================
        # RECALCULATE BILL TOTALS
        # ====================================================

        db.flush()

        items = (
            db.query(BillItem)
            .filter(BillItem.bill_id == bill_id)
            .all()
        )

        subtotal = 0
        gst_amount = 0

        for item in items:

            item_subtotal = (
                item.quantity *
                item.unit_price
            )

            item.gst_amount = (
                item_subtotal *
                item.gst_rate /
                100
            )

            item.total_amount = (
                item_subtotal +
                item.gst_amount
            )

            subtotal += item_subtotal
            gst_amount += item.gst_amount

        bill.subtotal = subtotal
        bill.gst_amount = gst_amount
        bill.total_amount = subtotal + gst_amount

        db.commit()
        db.refresh(bill)

        return {
            "success": True,
            "message": "Bill item updated successfully.",
            "bill_id": bill.id,
            "product": product.name,
            "sku": product.sku,
            "quantity": quantity,
            "subtotal": bill.subtotal,
            "gst_amount": bill.gst_amount,
            "total_amount": bill.total_amount
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error updating bill item: {str(e)}"
        }

    finally:
        db.close()


# ============================================================
# GET BILL
# ============================================================

def get_bill(bill_id):
    db = SessionLocal()

    try:
        # Find bill
        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:
            return {
                "success": False,
                "message": f"Bill with ID {bill_id} not found."
            }

        # Get bill items
        items = (
            db.query(BillItem)
            .filter(BillItem.bill_id == bill_id)
            .all()
        )

        bill_items = []

        for item in items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            if not product:
                continue

            bill_items.append({
                "product": product.name,
                "sku": product.sku,
                "quantity": item.quantity,
                "unit": product.unit,
                "unit_price": item.unit_price,
                "gst_rate": item.gst_rate,
                "gst_amount": item.gst_amount,
                "total_amount": item.total_amount
            })

        return {
            "success": True,
            "bill_id": bill.id,
            "status": bill.status,
            "customer_id": bill.customer_id,
            "payment_mode": bill.payment_mode,
            "items": bill_items,
            "subtotal": bill.subtotal,
            "gst_amount": bill.gst_amount,
            "total_amount": bill.total_amount,
            "created_at": (
                bill.created_at.isoformat()
                if bill.created_at
                else None
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": f"Error retrieving bill: {str(e)}"
        }

    finally:
        db.close()