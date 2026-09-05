from app.database.db import (
    SessionLocal,
    begin_write_transaction
)

from app.database.models import Product


# ============================================================
# MONEY / VALIDATION HELPERS
# ============================================================

def _is_valid_non_negative_number(value):
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def _is_positive_number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


# ============================================================
# ADD PRODUCT
# ============================================================

def add_product(
    name,
    sku,
    unit,
    cost_price,
    selling_price,
    mrp,
    quantity,
    reorder_level,
    gst_rate,
    hsn_code
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not name or not name.strip():

            return {
                "success": False,
                "message": "Product name cannot be empty."
            }

        if not sku or not sku.strip():

            return {
                "success": False,
                "message": "SKU cannot be empty."
            }

        if not unit or not unit.strip():

            return {
                "success": False,
                "message": "Unit cannot be empty."
            }

        if not hsn_code or not str(hsn_code).strip():

            return {
                "success": False,
                "message": "HSN code cannot be empty."
            }

        # ----------------------------------------------------
        # Numeric validation
        # ----------------------------------------------------

        if not _is_valid_non_negative_number(
            cost_price
        ):

            return {
                "success": False,
                "message": "Cost price must be zero or greater."
            }

        if not _is_valid_non_negative_number(
            selling_price
        ):

            return {
                "success": False,
                "message": "Selling price must be zero or greater."
            }

        if not _is_valid_non_negative_number(
            mrp
        ):

            return {
                "success": False,
                "message": "MRP must be zero or greater."
            }

        if not _is_valid_non_negative_number(
            quantity
        ):

            return {
                "success": False,
                "message": "Quantity cannot be negative."
            }

        if not _is_valid_non_negative_number(
            reorder_level
        ):

            return {
                "success": False,
                "message": "Reorder level cannot be negative."
            }

        try:
            gst_rate = float(gst_rate)
        except (TypeError, ValueError):

            return {
                "success": False,
                "message": "GST rate must be a number."
            }

        if gst_rate < 0 or gst_rate > 100:

            return {
                "success": False,
                "message": "GST rate must be between 0% and 100%."
            }

        cost_price = float(cost_price)
        selling_price = float(selling_price)
        mrp = float(mrp)
        quantity = float(quantity)
        reorder_level = float(reorder_level)

        # ----------------------------------------------------
        # BUSINESS GUARDRAIL:
        # Never sell below cost.
        # ----------------------------------------------------

        if selling_price < cost_price:

            return {
                "success": False,
                "message": (
                    f"Cannot add product with selling price "
                    f"₹{selling_price:.2f} below cost price "
                    f"₹{cost_price:.2f}."
                )
            }

        # ----------------------------------------------------
        # BUSINESS GUARDRAIL:
        # Selling price cannot exceed MRP.
        # ----------------------------------------------------

        if selling_price > mrp:

            return {
                "success": False,
                "message": (
                    f"Selling price ₹{selling_price:.2f} "
                    f"cannot exceed MRP ₹{mrp:.2f}."
                )
            }

        # ----------------------------------------------------
        # Lock database for write
        # ----------------------------------------------------

        begin_write_transaction(db)

        existing = (
            db.query(Product)
            .filter(
                Product.sku == sku.strip()
            )
            .first()
        )

        if existing:

            return {
                "success": False,
                "message": (
                    f"Product with SKU '{sku}' already exists."
                )
            }

        product = Product(
            name=name.strip(),
            sku=sku.strip(),
            unit=unit.strip(),
            cost_price=cost_price,
            selling_price=selling_price,
            mrp=mrp,
            quantity=quantity,
            reorder_level=reorder_level,
            gst_rate=gst_rate,
            hsn_code=str(hsn_code).strip()
        )

        db.add(product)

        db.commit()
        db.refresh(product)

        return {
            "success": True,
            "message": "Product added successfully.",
            "product_id": product.id,
            "name": product.name,
            "sku": product.sku,
            "unit": product.unit,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "mrp": product.mrp,
            "quantity": product.quantity,
            "reorder_level": product.reorder_level,
            "gst_rate": product.gst_rate,
            "hsn_code": product.hsn_code
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error adding product: {str(e)}"
            )
        }

    finally:

        db.close()


# ============================================================
# RECEIVE STOCK
# ============================================================

def receive_stock(
    sku,
    quantity,
    cost_price=None,
    mrp=None
):

    db = SessionLocal()

    try:

        if not _is_positive_number(
            quantity
        ):

            return {
                "success": False,
                "message": (
                    "Received quantity must be greater than zero."
                )
            }

        quantity = float(quantity)

        if cost_price is not None:

            if not _is_valid_non_negative_number(
                cost_price
            ):

                return {
                    "success": False,
                    "message": (
                        "Cost price must be zero or greater."
                    )
                }

            cost_price = float(cost_price)

        if mrp is not None:

            if not _is_valid_non_negative_number(
                mrp
            ):

                return {
                    "success": False,
                    "message": (
                        "MRP must be zero or greater."
                    )
                }

            mrp = float(mrp)

        # ----------------------------------------------------
        # Acquire write lock BEFORE reading stock.
        # ----------------------------------------------------

        begin_write_transaction(db)

        product = (
            db.query(Product)
            .filter(
                Product.sku == sku
            )
            .first()
        )

        if not product:

            return {
                "success": False,
                "message": (
                    f"Product with SKU '{sku}' not found."
                )
            }

        # ----------------------------------------------------
        # If cost changes, selling price must still not be
        # below the new cost.
        # ----------------------------------------------------

        if cost_price is not None:

            if product.selling_price < cost_price:

                return {
                    "success": False,
                    "message": (
                        f"Cannot update cost price to "
                        f"₹{cost_price:.2f} because the current "
                        f"selling price is only "
                        f"₹{product.selling_price:.2f}. "
                        "Selling below cost is not allowed."
                    )
                }

        # ----------------------------------------------------
        # MRP guard
        # ----------------------------------------------------

        if mrp is not None:

            if product.selling_price > mrp:

                return {
                    "success": False,
                    "message": (
                        f"MRP ₹{mrp:.2f} cannot be below the "
                        f"current selling price "
                        f"₹{product.selling_price:.2f}."
                    )
                }

        old_quantity = product.quantity

        product.quantity += quantity

        if cost_price is not None:
            product.cost_price = cost_price

        if mrp is not None:
            product.mrp = mrp

        db.commit()
        db.refresh(product)

        return {
            "success": True,
            "message": "Stock received successfully.",
            "sku": product.sku,
            "product": product.name,
            "previous_quantity": old_quantity,
            "received_quantity": quantity,
            "new_quantity": product.quantity,
            "unit": product.unit,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "mrp": product.mrp
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error receiving stock: {str(e)}"
            )
        }

    finally:

        db.close()


# ============================================================
# CHECK STOCK
# ============================================================

def check_stock(sku):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.sku == sku
            )
            .first()
        )

        if not product:

            return {
                "success": False,
                "message": (
                    f"Product with SKU '{sku}' not found."
                )
            }

        return {
            "success": True,
            "product": product.name,
            "sku": product.sku,
            "quantity": product.quantity,
            "unit": product.unit,
            "reorder_level": product.reorder_level,
            "selling_price": product.selling_price,
            "mrp": product.mrp,
            "gst_rate": product.gst_rate,
            "hsn_code": product.hsn_code
        }

    finally:

        db.close()


# ============================================================
# LOW STOCK
# ============================================================

def low_stock():

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .filter(
                Product.quantity <= Product.reorder_level
            )
            .all()
        )

        if not products:

            return {
                "success": True,
                "message": (
                    "No products are currently low in stock."
                ),
                "products": []
            }

        results = []

        for product in products:

            results.append(
                {
                    "product": product.name,
                    "sku": product.sku,
                    "quantity": product.quantity,
                    "unit": product.unit,
                    "reorder_level": product.reorder_level
                }
            )

        return {
            "success": True,
            "message": (
                f"{len(results)} product(s) are low in stock."
            ),
            "products": results
        }

    finally:

        db.close()