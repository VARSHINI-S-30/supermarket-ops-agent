from app.database.db import SessionLocal
from app.database.models import Product


def search_products(query):
    db = SessionLocal()

    try:
        if not query or not query.strip():
            return {
                "success": False,
                "message": "Search query cannot be empty."
            }

        query = query.strip().lower()

        products = (
            db.query(Product)
            .filter(
                Product.name.ilike(f"%{query}%")
            )
            .all()
        )

        if not products:
            return {
                "success": True,
                "message": "No products found.",
                "products": []
            }

        results = []

        for product in products:
            results.append({
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "unit": product.unit,
                "selling_price": product.selling_price,
                "mrp": product.mrp,
                "quantity": product.quantity,
                "reorder_level": product.reorder_level,
                "gst_rate": product.gst_rate,
                "hsn_code": product.hsn_code
            })

        return {
            "success": True,
            "message": f"Found {len(results)} product(s).",
            "products": results
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error searching products: {str(e)}"
        }

    finally:
        db.close()