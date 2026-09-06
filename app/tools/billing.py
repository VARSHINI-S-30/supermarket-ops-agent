from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

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


# ============================================================
# CONSTANTS
# ============================================================

MONEY_PLACES = Decimal("0.01")

ALLOWED_PAYMENT_MODES = {
    "cash",
    "upi",
    "card",
    "credit"
}


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    """
    Convert a numeric value to Decimal rounded to 2 decimal places.
    """

    try:
        return Decimal(str(value)).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP
        )

    except (InvalidOperation, ValueError, TypeError):

        raise ValueError(
            f"Invalid monetary value: {value}"
        )


# ============================================================
# QUANTITY HELPER
# ============================================================

def decimal_quantity(value):
    """
    Convert quantity to Decimal safely.
    """

    try:

        quantity = Decimal(str(value))

    except (InvalidOperation, ValueError, TypeError):

        raise ValueError(
            "Quantity must be a valid number."
        )

    if not quantity.is_finite():

        raise ValueError(
            "Quantity must be a finite number."
        )

    return quantity


# ============================================================
# CALCULATE ITEM AMOUNTS
# ============================================================

def calculate_item_amounts(
    quantity,
    unit_price,
    gst_rate
):
    """
    Calculate taxable amount, GST and total amount.
    """

    quantity = decimal_quantity(quantity)

    if quantity <= 0:

        raise ValueError(
            "Quantity must be greater than zero."
        )

    unit_price = money(unit_price)

    gst_rate = Decimal(str(gst_rate))

    if not gst_rate.is_finite():

        raise ValueError(
            "GST rate must be a finite number."
        )

    if gst_rate < 0 or gst_rate > 100:

        raise ValueError(
            "GST rate must be between 0 and 100."
        )

    taxable_amount = money(
        quantity * unit_price
    )

    gst_amount = money(
        taxable_amount
        * gst_rate
        / Decimal("100")
    )

    total_amount = money(
        taxable_amount + gst_amount
    )

    return {
        "taxable_amount": taxable_amount,
        "gst_amount": gst_amount,
        "total_amount": total_amount
    }


# ============================================================
# CREATE BILL
# ============================================================

def create_bill(customer_id=None):
    """
    Create a new draft bill.

    Customer ID is optional.

    A customer is required only when the bill is
    eventually finalized using credit/khata.
    """

    db = SessionLocal()

    try:

        begin_write_transaction(db)

        # ----------------------------------------------------
        # Validate customer
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Create draft bill
        # ----------------------------------------------------

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
            "subtotal": 0.00,
            "gst_amount": 0.00,
            "total_amount": 0.00,
            "message": (
                f"Draft bill #{bill.id} "
                "created successfully."
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


# ============================================================
# RECALCULATE BILL
# ============================================================

def _recalculate_bill(db, bill):
    """
    Recalculate subtotal, GST and total for a bill.
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


# ============================================================
# FIND PRODUCT BY SKU
# ============================================================

def _get_product_by_sku(db, sku):
    """
    Retrieve a product using its SKU.
    """

    if sku is None:

        return None

    sku = str(sku).strip()

    if not sku:

        return None

    return (
        db.query(Product)
        .filter(Product.sku == sku)
        .first()
    )


# ============================================================
# VALIDATE PRODUCT SELLING RULES
# ============================================================

def _validate_product_price(product):
    """
    Validate supermarket pricing rules.
    """

    cost_price = Decimal(
        str(product.cost_price)
    )

    selling_price = Decimal(
        str(product.selling_price)
    )

    mrp = Decimal(
        str(product.mrp)
    )

    if selling_price < cost_price:

        return {
            "success": False,
            "message": (
                f"Product '{product.name}' has a "
                "selling price below cost price."
            )
        }

    if selling_price > mrp:

        return {
            "success": False,
            "message": (
                f"Product '{product.name}' has a "
                "selling price above MRP."
            )
        }

    return {
        "success": True
    }


# ============================================================
# ADD ITEM TO BILL
# ============================================================

def add_item_to_bill(
    bill_id,
    sku,
    quantity
):
    """
    Add a product to a draft bill using SKU.

    Stock is checked at the database/tool layer.

    Overselling is prevented.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Lock database for write operation
        # ----------------------------------------------------

        begin_write_transaction(db)

        # ----------------------------------------------------
        # Validate bill ID
        # ----------------------------------------------------

        try:

            bill_id = int(bill_id)

        except (ValueError, TypeError):

            return {
                "success": False,
                "message": "Bill ID must be a valid integer."
            }

        # ----------------------------------------------------
        # Find bill
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Bill must be draft
        # ----------------------------------------------------

        if bill.status != "draft":

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} is already "
                    f"{bill.status} and cannot be edited."
                )
            }

        # ----------------------------------------------------
        # Validate quantity
        # ----------------------------------------------------

        try:

            quantity = decimal_quantity(quantity)

        except ValueError as e:

            return {
                "success": False,
                "message": str(e)
            }

        if quantity <= 0:

            return {
                "success": False,
                "message": (
                    "Quantity must be greater than zero."
                )
            }

        # ----------------------------------------------------
        # Validate SKU
        # ----------------------------------------------------

        if sku is None or not str(sku).strip():

            return {
                "success": False,
                "message": "Product SKU is required."
            }

        sku = str(sku).strip()

        # ----------------------------------------------------
        # Find product by SKU
        # ----------------------------------------------------

        product = _get_product_by_sku(
            db,
            sku
        )

        if not product:

            return {
                "success": False,
                "message": (
                    f"No product was found with SKU '{sku}'."
                )
            }

        # ----------------------------------------------------
        # Validate pricing
        # ----------------------------------------------------

        price_validation = _validate_product_price(
            product
        )

        if not price_validation["success"]:

            return price_validation

        # ----------------------------------------------------
        # Check existing bill item
        # ----------------------------------------------------

        existing_item = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id,
                BillItem.product_id == product.id
            )
            .first()
        )

        existing_quantity = Decimal("0.00")

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

        # ----------------------------------------------------
        # OVERSALE GUARD
        # ----------------------------------------------------

        if requested_total_quantity > available_stock:

            return {
                "success": False,
                "message": (
                    f"Insufficient stock for "
                    f"'{product.name}'. "
                    f"Available: {product.quantity} "
                    f"{product.unit}. "
                    f"Already in bill: "
                    f"{existing_quantity}. "
                    f"Additional requested: "
                    f"{quantity}. "
                    f"Total requested: "
                    f"{requested_total_quantity}."
                )
            }

        # ----------------------------------------------------
        # Existing item
        # ----------------------------------------------------

        if existing_item:

            existing_item.quantity = (
                requested_total_quantity
            )

            existing_item.unit_price = money(
                product.selling_price
            )

            existing_item.gst_rate = Decimal(
                str(product.gst_rate)
            )

            amounts = calculate_item_amounts(
                requested_total_quantity,
                product.selling_price,
                product.gst_rate
            )

            existing_item.gst_amount = (
                amounts["gst_amount"]
            )

            existing_item.total_amount = (
                amounts["total_amount"]
            )

        # ----------------------------------------------------
        # New item
        # ----------------------------------------------------

        else:

            amounts = calculate_item_amounts(
                quantity,
                product.selling_price,
                product.gst_rate
            )

            new_item = BillItem(
                bill_id=bill_id,
                product_id=product.id,
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

            db.add(new_item)

        # ----------------------------------------------------
        # Recalculate bill
        # ----------------------------------------------------

        db.flush()

        db.refresh(bill)

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
            "sku": product.sku,
            "unit": product.unit,
            "quantity_added": float(quantity),
            "bill_item_quantity": float(
                requested_total_quantity
            ),
            "available_stock": float(
                available_stock
            ),
            "bill_subtotal": float(
                bill.subtotal
            ),
            "bill_gst": float(
                bill.gst_amount
            ),
            "bill_total": float(
                bill.total_amount
            ),
            "message": (
                f"Added {quantity} {product.unit} "
                f"of {product.name} to bill "
                f"#{bill.id}. "
                f"Bill total: ₹{bill.total_amount:.2f}"
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


# ============================================================
# UPDATE BILL ITEM
# ============================================================

def update_bill_item(
    bill_id,
    sku,
    quantity
):
    """
    Update the quantity of an existing bill item.

    SKU is used to identify the product.

    Quantity zero removes the item.
    """

    db = SessionLocal()

    try:

        begin_write_transaction(db)

        # ----------------------------------------------------
        # Validate bill ID
        # ----------------------------------------------------

        try:

            bill_id = int(bill_id)

        except (ValueError, TypeError):

            return {
                "success": False,
                "message": "Bill ID must be a valid integer."
            }

        # ----------------------------------------------------
        # Find bill
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Check status
        # ----------------------------------------------------

        if bill.status != "draft":

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} cannot be edited "
                    f"because it is {bill.status}."
                )
            }

        # ----------------------------------------------------
        # Validate quantity
        # ----------------------------------------------------

        try:

            quantity = decimal_quantity(quantity)

        except ValueError as e:

            return {
                "success": False,
                "message": str(e)
            }

        # ----------------------------------------------------
        # Find product
        # ----------------------------------------------------

        product = _get_product_by_sku(
            db,
            sku
        )

        if not product:

            return {
                "success": False,
                "message": (
                    f"No product was found with SKU "
                    f"'{sku}'."
                )
            }

        # ----------------------------------------------------
        # Find bill item
        # ----------------------------------------------------

        item = (
            db.query(BillItem)
            .filter(
                BillItem.bill_id == bill_id,
                BillItem.product_id == product.id
            )
            .first()
        )

        if not item:

            return {
                "success": False,
                "message": (
                    f"'{product.name}' is not present "
                    "in the bill."
                )
            }

        # ----------------------------------------------------
        # Remove item
        # ----------------------------------------------------

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
                "product_name": product.name,
                "message": (
                    f"Removed {product.name} "
                    f"from bill #{bill.id}."
                ),
                "bill_subtotal": float(
                    bill.subtotal
                ),
                "bill_gst": float(
                    bill.gst_amount
                ),
                "bill_total": float(
                    bill.total_amount
                )
            }

        # ----------------------------------------------------
        # Validate pricing
        # ----------------------------------------------------

        price_validation = _validate_product_price(
            product
        )

        if not price_validation["success"]:

            return price_validation

        # ----------------------------------------------------
        # Check stock
        # ----------------------------------------------------

        available_stock = Decimal(
            str(product.quantity)
        )

        if quantity > available_stock:

            return {
                "success": False,
                "message": (
                    f"Insufficient stock for "
                    f"'{product.name}'. "
                    f"Available: {product.quantity} "
                    f"{product.unit}. "
                    f"Requested: {quantity}."
                )
            }

        # ----------------------------------------------------
        # Update item
        # ----------------------------------------------------

        item.quantity = quantity

        item.unit_price = money(
            product.selling_price
        )

        item.gst_rate = Decimal(
            str(product.gst_rate)
        )

        amounts = calculate_item_amounts(
            quantity,
            product.selling_price,
            product.gst_rate
        )

        item.gst_amount = (
            amounts["gst_amount"]
        )

        item.total_amount = (
            amounts["total_amount"]
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
            "product_name": product.name,
            "sku": product.sku,
            "quantity": float(quantity),
            "bill_subtotal": float(
                bill.subtotal
            ),
            "bill_gst": float(
                bill.gst_amount
            ),
            "bill_total": float(
                bill.total_amount
            ),
            "message": (
                f"Updated {product.name} quantity "
                f"to {quantity} in bill #{bill.id}. "
                f"Bill total: "
                f"₹{bill.total_amount:.2f}"
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


# ============================================================
# GET DEFAULT PAYMENT
# ============================================================

def _get_default_payment():
    """
    Read the persistent default payment preference.
    """

    result = get_preference(
        "default_payment"
    )

    if not result.get("success"):

        return None

    if not result.get("found"):

        return None

    value = result.get(
        "preference_value"
    )

    if not value:

        return None

    payment_mode = str(
        value
    ).strip().lower()

    if payment_mode not in ALLOWED_PAYMENT_MODES:

        return None

    return payment_mode


# ============================================================
# FINALIZE BILL
# ============================================================

def finalize_bill(
    bill_id,
    payment_mode=None
):
    """
    Finalize a draft bill.

    Features:
    - Persistent default payment
    - Explicit payment overrides default
    - Credit validation
    - Final stock recheck
    - Price validation
    - GST recalculation
    - Atomic stock deduction
    - Idempotent finalization
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Lock database for entire finalization operation
        # ----------------------------------------------------

        begin_write_transaction(db)

        # ----------------------------------------------------
        # Validate bill ID
        # ----------------------------------------------------

        try:

            bill_id = int(bill_id)

        except (ValueError, TypeError):

            return {
                "success": False,
                "message": "Bill ID must be a valid integer."
            }

        # ----------------------------------------------------
        # Get bill
        # ----------------------------------------------------

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

        # ====================================================
        # IDEMPOTENCY
        # ====================================================

        if bill.status == "finalized":

            return {
                "success": True,
                "idempotent": True,
                "bill_id": bill.id,
                "status": bill.status,
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
                "message": (
                    f"Bill #{bill.id} was already "
                    "finalized. No additional stock "
                    "was deducted and no additional "
                    "credit was created."
                )
            }

        # ----------------------------------------------------
        # Bill must be draft
        # ----------------------------------------------------

        if bill.status != "draft":

            return {
                "success": False,
                "message": (
                    f"Bill #{bill.id} cannot be finalized "
                    f"because its status is {bill.status}."
                )
            }

        # ====================================================
        # PAYMENT MODE
        # ====================================================

        # Explicit payment mode has priority.
        if payment_mode is not None:

            payment_mode = str(
                payment_mode
            ).strip().lower()

        # If missing, use persistent default.
        else:

            payment_mode = _get_default_payment()

        # ----------------------------------------------------
        # No payment mode
        # ----------------------------------------------------

        if not payment_mode:

            return {
                "success": False,
                "message": (
                    "Payment mode was not provided and "
                    "no default payment preference is saved. "
                    "Please specify cash, UPI, card, or credit."
                )
            }

        # ----------------------------------------------------
        # Validate payment mode
        # ----------------------------------------------------

        if payment_mode not in ALLOWED_PAYMENT_MODES:

            return {
                "success": False,
                "message": (
                    "Invalid payment mode. "
                    "Allowed values: cash, upi, card, credit."
                )
            }

        # ====================================================
        # EMPTY BILL
        # ====================================================

        if not bill.items:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill.id} has no items. "
                    "Add at least one product before finalizing."
                )
            }

        # ====================================================
        # CREDIT VALIDATION
        # ====================================================

        customer = None

        if payment_mode == "credit":

            if not bill.customer_id:

                return {
                    "success": False,
                    "message": (
                        "Credit payment requires a customer "
                        "to be associated with the bill."
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
                        "The customer associated with "
                        "this bill was not found."
                    )
                }

        # ====================================================
        # FINAL STOCK + PRICE VALIDATION
        # ====================================================

        products = {}

        for item in bill.items:

            product = (
                db.query(Product)
                .filter(
                    Product.id == item.product_id
                )
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

            products[item.product_id] = product

            # ------------------------------------------------
            # Quantity
            # ------------------------------------------------

            requested_quantity = Decimal(
                str(item.quantity)
            )

            if requested_quantity <= 0:

                return {
                    "success": False,
                    "message": (
                        f"Invalid quantity for "
                        f"'{product.name}'."
                    )
                }

            # ------------------------------------------------
            # Stock
            # ------------------------------------------------

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
                        f"Available: "
                        f"{product.quantity} "
                        f"{product.unit}. "
                        f"Required: "
                        f"{item.quantity}."
                    )
                }

            # ------------------------------------------------
            # Price validation
            # ------------------------------------------------

            price_validation = (
                _validate_product_price(
                    product
                )
            )

            if not price_validation["success"]:

                return {
                    "success": False,
                    "message": (
                        f"Cannot finalize bill "
                        f"#{bill.id}. "
                        f"{price_validation['message']}"
                    )
                }

            # ------------------------------------------------
            # GST validation
            # ------------------------------------------------

            gst_rate = Decimal(
                str(product.gst_rate)
            )

            if gst_rate < 0 or gst_rate > 100:

                return {
                    "success": False,
                    "message": (
                        f"Invalid GST rate for "
                        f"'{product.name}'."
                    )
                }

        # ====================================================
        # FINAL BILL RECALCULATION
        # ====================================================

        _recalculate_bill(
            db,
            bill
        )

        db.flush()

        # ====================================================
        # ATOMIC STOCK DEDUCTION
        # ====================================================

        for item in bill.items:

            product = products[
                item.product_id
            ]

            quantity = Decimal(
                str(item.quantity)
            )

            current_stock = Decimal(
                str(product.quantity)
            )

            # Final safety check.
            if current_stock < quantity:

                return {
                    "success": False,
                    "message": (
                        f"Stock changed while finalizing "
                        f"bill #{bill.id}. "
                        f"Transaction cancelled."
                    )
                }

            product.quantity = (
                current_stock - quantity
            )

            # Never permit negative stock.
            if product.quantity < 0:

                return {
                    "success": False,
                    "message": (
                        "Stock cannot become negative. "
                        "Transaction cancelled."
                    )
                }

        # ====================================================
        # CREDIT UPDATE
        # ====================================================

        if payment_mode == "credit":

            current_credit = Decimal(
                str(customer.credit_balance)
            )

            customer.credit_balance = money(
                current_credit
                + Decimal(
                    str(bill.total_amount)
                )
            )

        # ====================================================
        # FINALIZE BILL
        # ====================================================

        bill.status = "finalized"

        bill.payment_mode = payment_mode

        db.flush()

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
                f"Bill #{bill.id} finalized "
                f"successfully using "
                f"{payment_mode.upper()}. "
                f"Total: "
                f"₹{bill.total_amount:.2f}"
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


# ============================================================
# GET BILL
# ============================================================

def get_bill(bill_id):
    """
    Retrieve complete bill information.

    Includes:
    - Product information
    - Quantity
    - Unit price
    - GST
    - CGST
    - SGST
    - Taxable amount
    - Total
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Validate ID
        # ----------------------------------------------------

        try:

            bill_id = int(bill_id)

        except (ValueError, TypeError):

            return {
                "success": False,
                "message": "Bill ID must be a valid integer."
            }

        # ----------------------------------------------------
        # Find bill
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Build item list
        # ----------------------------------------------------

        items = []

        for item in bill.items:

            product = (
                db.query(Product)
                .filter(
                    Product.id == item.product_id
                )
                .first()
            )

            # ------------------------------------------------
            # GST
            # ------------------------------------------------

            gst_amount = money(
                item.gst_amount
            )

            # Make CGST + SGST exactly equal GST.
            cgst_amount = money(
                gst_amount / Decimal("2")
            )

            sgst_amount = money(
                gst_amount - cgst_amount
            )

            # ------------------------------------------------
            # Taxable amount
            # ------------------------------------------------

            taxable_amount = money(
                Decimal(
                    str(item.quantity)
                )
                * Decimal(
                    str(item.unit_price)
                )
            )

            # ------------------------------------------------
            # Item data
            # ------------------------------------------------

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
                    taxable_amount
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

        # ----------------------------------------------------
        # Bill response
        # ----------------------------------------------------

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


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEBULA SUPERMARKET BILLING MODULE")
    print("=" * 60)

    print("\nBilling module loaded successfully.")

    print("\nSupported payment modes:")

    for mode in sorted(
        ALLOWED_PAYMENT_MODES
    ):

        print(
            f"- {mode}"
        )

    print("\nFunctions available:")

    print("- create_bill()")
    print("- add_item_to_bill()")
    print("- update_bill_item()")
    print("- get_bill()")
    print("- finalize_bill()")

    print("\nBilling module test completed.")