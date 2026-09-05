from decimal import Decimal, ROUND_HALF_UP

from app.database.db import (
    SessionLocal,
    begin_write_transaction
)

from app.database.models import (
    Bill,
    BillItem,
    Product,
    Customer
)

from app.tools.preferences import get_preference


MONEY_PLACES = Decimal("0.01")


def money(value):
    """
    Convert a numeric value to Decimal rounded to 2 decimal places.
    """
    return Decimal(str(value)).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP
    )


def calculate_item_amounts(quantity, unit_price, gst_rate):
    """
    Calculate taxable amount, GST and total amount.
    """

    quantity = Decimal(str(quantity))
    unit_price = money(unit_price)
    gst_rate = Decimal(str(gst_rate))

    taxable_amount = money(
        quantity * unit_price
    )

    gst_amount = money(
        taxable_amount * gst_rate / Decimal("100")
    )

    total_amount = money(
        taxable_amount + gst_amount
    )

    return {
        "taxable_amount": taxable_amount,
        "gst_amount": gst_amount,
        "total_amount": total_amount
    }


def create_bill(customer_id=None):
    """
    Create a new draft bill.
    """

    db = SessionLocal()

    try:

        begin_write_transaction(db)

        customer = None

        if customer_id is not None:

            customer = (
                db.query(Customer)
                .filter(Customer.id == customer_id)
                .first()
            )

            if not customer:

                return {
                    "success": False,
                    "message": (
                        f"Customer #{customer_id} "
                        "was not found."
                    )
                }

        bill = Bill(
            customer_id=customer_id,
            status="draft",
            subtotal=Decimal("0.00"),
            gst_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            payment_mode=None
        )

        db.add(bill)
        db.commit()
        db.refresh(bill)

        return {
            "success": True,
            "bill_id": bill.id,
            "status": bill.status,
            "customer_id": bill.customer_id,
            "message": (
                f"Draft bill #{bill.id} created successfully."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error creating bill: {str(e)}"
            )
        }

    finally:

        db.close()


def _recalculate_bill(db, bill):
    """
    Recalculate bill subtotal, GST and total.
    """

    subtotal = Decimal("0.00")
    gst_amount = Decimal("0.00")

    for item in bill.items:

        amounts = calculate_item_amounts(
            item.quantity,
            item.unit_price,
            item.gst_rate
        )

        item.gst_amount = amounts["gst_amount"]
        item.total_amount = amounts["total_amount"]

        subtotal += amounts["taxable_amount"]
        gst_amount += amounts["gst_amount"]

    bill.subtotal = money(subtotal)
    bill.gst_amount = money(gst_amount)

    bill.total_amount = money(
        subtotal + gst_amount
    )


def add_item_to_bill(
    bill_id,
    product_id,
    quantity
):
    """
    Add a product to a draft bill.

    Stock is checked and overselling is prevented.
    """

    db = SessionLocal()

    try:

        begin_write_transaction(db)

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} was not found."
                )
            }

        if bill.status != "draft":

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} is already "
                    f"{bill.status} and cannot be edited."
                )
            }

        try:
            quantity = Decimal(str(quantity))
        except Exception:

            return {
                "success": False,
                "message": "Quantity must be a valid number."
            }

        if quantity <= 0:

            return {
                "success": False,
                "message": (
                    "Quantity must be greater than zero."
                )
            }

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if not product:

            return {
                "success": False,
                "message": (
                    f"Product #{product_id} was not found."
                )
            }

        if product.selling_price < product.cost_price:

            return {
                "success": False,
                "message": (
                    f"Product '{product.name}' has a selling "
                    "price below cost price."
                )
            }

        if product.selling_price > product.mrp:

            return {
                "success": False,
                "message": (
                    f"Product '{product.name}' has a selling "
                    "price above MRP."
                )
            }

        existing_item = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id,
                BillItem.product_id == product_id
            )
            .first()
        )

        existing_quantity = Decimal("0")

        if existing_item:

            existing_quantity = Decimal(
                str(existing_item.quantity)
            )

        requested_total_quantity = (
            existing_quantity + quantity
        )

        available_stock = Decimal(
            str(product.quantity)
        )

        if requested_total_quantity > available_stock:

            return {
                "success": False,
                "message": (
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.quantity} "
                    f"{product.unit}. "
                    f"Requested: {requested_total_quantity}."
                )
            }

        if existing_item:

            existing_item.quantity = requested_total_quantity

            existing_item.unit_price = money(
                product.selling_price
            )

            existing_item.gst_rate = Decimal(
                str(product.gst_rate)
            )

        else:

            amounts = calculate_item_amounts(
                quantity,
                product.selling_price,
                product.gst_rate
            )

            existing_item = BillItem(
                bill_id=bill_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=money(
                    product.selling_price
                ),
                gst_rate=Decimal(
                    str(product.gst_rate)
                ),
                gst_amount=amounts["gst_amount"],
                total_amount=amounts["total_amount"]
            )

            db.add(existing_item)

        db.flush()

        _recalculate_bill(
            db,
            bill
        )

        db.commit()

        return {
            "success": True,
            "bill_id": bill.id,
            "product_id": product.id,
            "product_name": product.name,
            "quantity_added": float(quantity),
            "bill_subtotal": float(bill.subtotal),
            "bill_gst": float(bill.gst_amount),
            "bill_total": float(bill.total_amount),
            "message": (
                f"Added {quantity} {product.unit} "
                f"of {product.name} to bill #{bill.id}."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error adding item to bill: {str(e)}"
            )
        }

    finally:

        db.close()


def update_bill_item(
    bill_id,
    product_id,
    quantity
):
    """
    Update quantity of an existing bill item.
    """

    db = SessionLocal()

    try:

        begin_write_transaction(db)

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} was not found."
                )
            }

        if bill.status != "draft":

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} cannot be edited "
                    f"because it is {bill.status}."
                )
            }

        try:
            quantity = Decimal(str(quantity))
        except Exception:

            return {
                "success": False,
                "message": "Quantity must be a valid number."
            }

        item = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id,
                BillItem.product_id == product_id
            )
            .first()
        )

        if not item:

            return {
                "success": False,
                "message": (
                    "That product is not present "
                    "in the bill."
                )
            }

        if quantity <= 0:

            db.delete(item)

            db.flush()

            _recalculate_bill(
                db,
                bill
            )

            db.commit()

            return {
                "success": True,
                "bill_id": bill.id,
                "message": (
                    "Bill item removed because "
                    "quantity was zero or negative."
                )
            }

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:

            return {
                "success": False,
                "message": "Product no longer exists."
            }

        available_stock = Decimal(
            str(product.quantity)
        )

        if quantity > available_stock:

            return {
                "success": False,
                "message": (
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.quantity} "
                    f"{product.unit}."
                )
            }

        item.quantity = quantity
        item.unit_price = money(
            product.selling_price
        )
        item.gst_rate = Decimal(
            str(product.gst_rate)
        )

        db.flush()

        _recalculate_bill(
            db,
            bill
        )

        db.commit()

        return {
            "success": True,
            "bill_id": bill.id,
            "product_id": product.id,
            "quantity": float(quantity),
            "bill_subtotal": float(bill.subtotal),
            "bill_gst": float(bill.gst_amount),
            "bill_total": float(bill.total_amount),
            "message": (
                f"Updated bill #{bill.id}."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error updating bill: {str(e)}"
            )
        }

    finally:

        db.close()


def _get_default_payment():
    """
    Read the persistent default payment preference.
    """

    result = get_preference(
        "default_payment"
    )

    if (
        result.get("success")
        and result.get("found")
        and result.get("preference_value")
    ):

        return result["preference_value"].lower()

    return None


def finalize_bill(
    bill_id,
    payment_mode=None
):
    """
    Finalize a bill.

    If payment_mode is not supplied, the persistent
    default_payment preference is used.

    Explicit payment mode always overrides the default.
    """

    db = SessionLocal()

    try:

        begin_write_transaction(db)

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} was not found."
                )
            }

        # --------------------------------------------------
        # IDEMPOTENCY
        # --------------------------------------------------

        if bill.status == "finalized":

            return {
                "success": True,
                "idempotent": True,
                "bill_id": bill.id,
                "payment_mode": bill.payment_mode,
                "total_amount": float(
                    bill.total_amount
                ),
                "message": (
                    f"Bill #{bill.id} was already finalized. "
                    "No additional stock was deducted."
                )
            }

        if bill.status != "draft":

            return {
                "success": False,
                "message": (
                    f"Bill #{bill.id} cannot be finalized "
                    f"because its status is {bill.status}."
                )
            }

        # --------------------------------------------------
        # PAYMENT MODE
        # --------------------------------------------------

        if payment_mode is None or not str(
            payment_mode
        ).strip():

            payment_mode = _get_default_payment()

        if payment_mode is None:

            return {
                "success": False,
                "message": (
                    "Payment mode was not provided and "
                    "no default payment preference is saved."
                )
            }

        payment_mode = str(
            payment_mode
        ).strip().lower()

        allowed_payment_modes = {
            "cash",
            "upi",
            "card",
            "credit"
        }

        if payment_mode not in allowed_payment_modes:

            return {
                "success": False,
                "message": (
                    "Invalid payment mode. "
                    "Allowed values: cash, upi, card, credit."
                )
            }

        # --------------------------------------------------
        # EMPTY BILL
        # --------------------------------------------------

        if not bill.items:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill.id} has no items."
                )
            }

        # --------------------------------------------------
        # CREDIT VALIDATION
        # --------------------------------------------------

        customer = None

        if payment_mode == "credit":

            if not bill.customer_id:

                return {
                    "success": False,
                    "message": (
                        "Credit payment requires a customer."
                    )
                }

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id == bill.customer_id
                )
                .first()
            )

            if not customer:

                return {
                    "success": False,
                    "message": (
                        "Customer associated with "
                        "the bill was not found."
                    )
                }

        # --------------------------------------------------
        # RECHECK STOCK + PRICES
        # --------------------------------------------------

        for item in bill.items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            if not product:

                return {
                    "success": False,
                    "message": (
                        f"Product #{item.product_id} "
                        "no longer exists."
                    )
                }

            requested_quantity = Decimal(
                str(item.quantity)
            )

            available_quantity = Decimal(
                str(product.quantity)
            )

            if requested_quantity > available_quantity:

                return {
                    "success": False,
                    "message": (
                        f"Cannot finalize bill #{bill.id}. "
                        f"Insufficient stock for "
                        f"'{product.name}'. "
                        f"Available: {product.quantity} "
                        f"{product.unit}, "
                        f"required: {item.quantity}."
                    )
                }

            if product.selling_price < product.cost_price:

                return {
                    "success": False,
                    "message": (
                        f"Cannot finalize bill because "
                        f"'{product.name}' has a selling "
                        "price below cost."
                    )
                }

            if product.selling_price > product.mrp:

                return {
                    "success": False,
                    "message": (
                        f"Cannot finalize bill because "
                        f"'{product.name}' has a selling "
                        "price above MRP."
                    )
                }

        # --------------------------------------------------
        # FINAL RECALCULATION
        # --------------------------------------------------

        _recalculate_bill(
            db,
            bill
        )

        # --------------------------------------------------
        # DEDUCT STOCK
        # --------------------------------------------------

        for item in bill.items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            quantity = Decimal(
                str(item.quantity)
            )

            if Decimal(
                str(product.quantity)
            ) < quantity:

                return {
                    "success": False,
                    "message": (
                        f"Stock changed while finalizing "
                        f"bill #{bill.id}. "
                        "Transaction cancelled."
                    )
                }

            product.quantity = (
                Decimal(
                    str(product.quantity)
                ) - quantity
            )

            if product.quantity < 0:

                return {
                    "success": False,
                    "message": (
                        "Stock cannot become negative."
                    )
                }

        # --------------------------------------------------
        # CREDIT UPDATE
        # --------------------------------------------------

        if payment_mode == "credit":

            customer.credit_balance = money(
                Decimal(
                    str(customer.credit_balance)
                )
                + Decimal(
                    str(bill.total_amount)
                )
            )

        # --------------------------------------------------
        # FINALIZE
        # --------------------------------------------------

        bill.status = "finalized"
        bill.payment_mode = payment_mode

        db.commit()

        return {
            "success": True,
            "idempotent": False,
            "bill_id": bill.id,
            "status": bill.status,
            "payment_mode": payment_mode,
            "subtotal": float(
                bill.subtotal
            ),
            "gst_amount": float(
                bill.gst_amount
            ),
            "total_amount": float(
                bill.total_amount
            ),
            "message": (
                f"Bill #{bill.id} finalized successfully "
                f"using {payment_mode.upper()}."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error finalizing bill: {str(e)}"
            )
        }

    finally:

        db.close()


def get_bill(bill_id):
    """
    Retrieve complete bill information.
    """

    db = SessionLocal()

    try:

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} was not found."
                )
            }

        items = []

        for item in bill.items:

            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )

            gst_amount = money(
                item.gst_amount
            )

            cgst_amount = money(
                gst_amount / Decimal("2")
            )

            sgst_amount = money(
                gst_amount / Decimal("2")
            )

            items.append({
                "item_id": item.id,
                "product_id": item.product_id,
                "product_name": (
                    product.name
                    if product
                    else "Unknown Product"
                ),
                "sku": (
                    product.sku
                    if product
                    else None
                ),
                "unit": (
                    product.unit
                    if product
                    else None
                ),
                "quantity": float(
                    item.quantity
                ),
                "unit_price": float(
                    item.unit_price
                ),
                "gst_rate": float(
                    item.gst_rate
                ),
                "taxable_amount": float(
                    money(
                        Decimal(
                            str(item.quantity)
                        )
                        * Decimal(
                            str(item.unit_price)
                        )
                    )
                ),
                "cgst_amount": float(
                    cgst_amount
                ),
                "sgst_amount": float(
                    sgst_amount
                ),
                "gst_amount": float(
                    gst_amount
                ),
                "total_amount": float(
                    item.total_amount
                )
            })

        return {
            "success": True,
            "bill_id": bill.id,
            "status": bill.status,
            "customer_id": bill.customer_id,
            "payment_mode": bill.payment_mode,
            "subtotal": float(
                bill.subtotal
            ),
            "gst_amount": float(
                bill.gst_amount
            ),
            "total_amount": float(
                bill.total_amount
            ),
            "items": items
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error retrieving bill: {str(e)}"
            )
        }

    finally:

        db.close()