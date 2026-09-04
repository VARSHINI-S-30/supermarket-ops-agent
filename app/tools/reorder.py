from app.database.db import SessionLocal
from app.database.models import Product


def get_reorder_recommendations():
    db = SessionLocal()

    try:
        # Find products at or below their reorder level
        products = (
            db.query(Product)
            .filter(
                Product.quantity <= Product.reorder_level
            )
            .all()
        )

        # No products need reordering
        if not products:
            return {
                "success": True,
                "message": "No products need reordering.",
                "products": []
            }

        recommendations = []

        for product in products:

            # Target stock is twice the reorder level
            target_stock = product.reorder_level * 2

            # Suggested quantity to purchase
            reorder_quantity = (
                target_stock - product.quantity
            )

            if reorder_quantity < 0:
                reorder_quantity = 0

            recommendations.append({
                "product": product.name,
                "sku": product.sku,
                "current_stock": product.quantity,
                "unit": product.unit,
                "reorder_level": product.reorder_level,
                "suggested_reorder_quantity": reorder_quantity,
                "selling_price": product.selling_price,
                "cost_price": product.cost_price
            })

        return {
            "success": True,
            "message": (
                f"{len(recommendations)} product(s) "
                f"need reordering."
            ),
            "products": recommendations
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                "Error generating reorder recommendations: "
                f"{str(e)}"
            )
        }

    finally:
        db.close()