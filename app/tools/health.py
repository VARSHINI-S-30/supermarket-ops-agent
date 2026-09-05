from app.database.db import SessionLocal
from app.database.models import (
    Product,
    Customer,
    Bill,
    BillItem,
    OwnerPreference,
    TelegramSession
)


def get_system_health():
    """
    Check database and core supermarket entities.
    """

    db = SessionLocal()

    try:

        product_count = (
            db.query(Product).count()
        )

        customer_count = (
            db.query(Customer).count()
        )

        bill_count = (
            db.query(Bill).count()
        )

        bill_item_count = (
            db.query(BillItem).count()
        )

        preference_count = (
            db.query(OwnerPreference).count()
        )

        try:

            session_count = (
                db.query(TelegramSession).count()
            )

        except Exception:

            session_count = None

        negative_stock = (
            db.query(Product)
            .filter(Product.quantity < 0)
            .count()
        )

        draft_bills = (
            db.query(Bill)
            .filter(Bill.status == "draft")
            .count()
        )

        finalized_bills = (
            db.query(Bill)
            .filter(Bill.status == "finalized")
            .count()
        )

        if negative_stock > 0:

            status = "warning"

        else:

            status = "healthy"

        return {
            "success": True,
            "status": status,
            "database": "connected",
            "products": product_count,
            "customers": customer_count,
            "bills": bill_count,
            "bill_items": bill_item_count,
            "preferences": preference_count,
            "telegram_sessions": session_count,
            "negative_stock_items": negative_stock,
            "draft_bills": draft_bills,
            "finalized_bills": finalized_bills,
            "message": (
                "System health check completed."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "status": "error",
            "database": "error",
            "message": (
                f"Health check failed: {str(e)}"
            )
        }

    finally:

        db.close()