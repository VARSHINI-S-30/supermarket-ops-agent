from app.database.db import SessionLocal
from app.database.models import Product


def add_product(
    name,
    sku,
    unit,
    cost_price,
    selling_price,
    mrp,
    quantity=0,
    reorder_level=5,
    gst_rate=0,
    hsn_code=None
):
    db = SessionLocal()

    try:
        # Check if SKU already exists
        existing_product = (
            db.query(Product)
            .filter(Product.sku == sku)
            .first()
        )

        if existing_product:
            return {
                "success": False,
                "message": f"Product with SKU '{sku}' already exists."
            }

        # Prevent invalid prices
        if cost_price < 0 or selling_price < 0 or mrp < 0:
            return {
                "success": False,
                "message": "Prices cannot be negative."
            }

        if quantity < 0:
            return {
                "success": False,
                "message": "Quantity cannot be negative."
            }

        product = Product(
            name=name,
            sku=sku,
            unit=unit,
            cost_price=cost_price,
            selling_price=selling_price,
            mrp=mrp,
            quantity=quantity,
            reorder_level=reorder_level,
            gst_rate=gst_rate,
            hsn_code=hsn_code
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
            "quantity": product.quantity
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error adding product: {str(e)}"
        }

    finally:
        db.close()


def receive_stock(sku, quantity, cost_price=None, mrp=None):
    db = SessionLocal()

    try:
        if quantity <= 0:
            return {
                "success": False,
                "message": "Received quantity must be greater than zero."
            }

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
            "product": product.name,
            "sku": product.sku,
            "previous_stock": old_quantity,
            "received": quantity,
            "current_stock": product.quantity
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error receiving stock: {str(e)}"
        }

    finally:
        db.close()


def check_stock(sku):
    db = SessionLocal()

    try:
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

        return {
            "success": True,
            "product": product.name,
            "sku": product.sku,
            "quantity": product.quantity,
            "unit": product.unit,
            "reorder_level": product.reorder_level
        }

    finally:
        db.close()


def low_stock():
    db = SessionLocal()

    try:
        products = (
            db.query(Product)
            .filter(Product.quantity <= Product.reorder_level)
            .all()
        )

        result = []

        for product in products:
            result.append({
                "name": product.name,
                "sku": product.sku,
                "quantity": product.quantity,
                "reorder_level": product.reorder_level,
                "unit": product.unit
            })

        return {
            "success": True,
            "count": len(result),
            "products": result
        }

    finally:
        db.close()