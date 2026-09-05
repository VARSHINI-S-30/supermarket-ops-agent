from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func

from app.database.db import SessionLocal
from app.database.models import (
    Bill,
    BillItem,
    Product,
)


# =========================================================
# HELPERS
# =========================================================

def money(value):
    return Decimal(
        str(value or 0)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def parse_date(value):
    """
    Convert YYYY-MM-DD string into date object.
    """

    if isinstance(value, date):
        return value

    if not value:
        return None

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return None


def get_date_range(
    start_date=None,
    end_date=None
):
    """
    Return inclusive date range.

    If no dates are supplied,
    today's date is used.
    """

    if start_date:
        start = parse_date(start_date)

        if not start:
            raise ValueError(
                "start_date must use YYYY-MM-DD format."
            )
    else:
        start = date.today()

    if end_date:
        end = parse_date(end_date)

        if not end:
            raise ValueError(
                "end_date must use YYYY-MM-DD format."
            )
    else:
        end = start

    if end < start:
        raise ValueError(
            "end_date cannot be before start_date."
        )

    return start, end


def datetime_bounds(
    start_date,
    end_date
):
    """
    Convert dates into datetime boundaries.
    """

    start_datetime = datetime.combine(
        start_date,
        datetime.min.time()
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        datetime.min.time()
    )

    return start_datetime, end_datetime


# =========================================================
# SALES SUMMARY
# =========================================================

def get_sales_summary(
    start_date=None,
    end_date=None
):
    """
    Return sales summary for a date range.

    Includes:

    - total sales
    - subtotal
    - GST
    - bill count
    - average bill
    - payment breakdown
    - top products
    """

    db = SessionLocal()

    try:

        start, end = get_date_range(
            start_date,
            end_date
        )

        start_datetime, end_datetime = datetime_bounds(
            start,
            end
        )

        bills = (
            db.query(Bill)
            .filter(
                Bill.status == "finalized",
                Bill.created_at >= start_datetime,
                Bill.created_at < end_datetime
            )
            .order_by(
                Bill.created_at
            )
            .all()
        )

        total_subtotal = Decimal("0.00")
        total_gst = Decimal("0.00")
        total_sales = Decimal("0.00")

        payment_breakdown = {
            "cash": Decimal("0.00"),
            "upi": Decimal("0.00"),
            "card": Decimal("0.00"),
            "credit": Decimal("0.00"),
        }

        payment_bill_count = {
            "cash": 0,
            "upi": 0,
            "card": 0,
            "credit": 0,
        }

        for bill in bills:

            subtotal = money(
                bill.subtotal
            )

            gst = money(
                bill.gst_amount
            )

            total = money(
                bill.total_amount
            )

            total_subtotal += subtotal
            total_gst += gst
            total_sales += total

            payment_mode = (
                str(
                    bill.payment_mode or ""
                )
                .strip()
                .lower()
            )

            if payment_mode in payment_breakdown:

                payment_breakdown[
                    payment_mode
                ] += total

                payment_bill_count[
                    payment_mode
                ] += 1

        # -------------------------------------------------
        # TOP PRODUCTS
        # -------------------------------------------------

        top_rows = (
            db.query(
                Product.id,
                Product.name,
                Product.sku,
                func.sum(
                    BillItem.quantity
                ).label("quantity_sold"),
                func.sum(
                    BillItem.total_amount
                ).label("sales_amount")
            )
            .join(
                BillItem,
                BillItem.product_id == Product.id
            )
            .join(
                Bill,
                Bill.id == BillItem.bill_id
            )
            .filter(
                Bill.status == "finalized",
                Bill.created_at >= start_datetime,
                Bill.created_at < end_datetime
            )
            .group_by(
                Product.id,
                Product.name,
                Product.sku
            )
            .order_by(
                func.sum(
                    BillItem.quantity
                ).desc()
            )
            .limit(10)
            .all()
        )

        top_products = []

        for row in top_rows:

            top_products.append(
                {
                    "product_id": row.id,
                    "name": row.name,
                    "sku": row.sku,
                    "quantity_sold": float(
                        row.quantity_sold or 0
                    ),
                    "sales_amount": float(
                        money(
                            row.sales_amount
                        )
                    )
                }
            )

        bill_count = len(bills)

        if bill_count:
            average_bill = (
                total_sales
                / Decimal(str(bill_count))
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        else:
            average_bill = Decimal("0.00")

        return {
            "success": True,
            "start_date": str(start),
            "end_date": str(end),
            "bill_count": bill_count,
            "subtotal": float(
                money(total_subtotal)
            ),
            "gst_collected": float(
                money(total_gst)
            ),
            "total_sales": float(
                money(total_sales)
            ),
            "average_bill": float(
                average_bill
            ),
            "payment_breakdown": {
                key: float(
                    money(value)
                )
                for key, value
                in payment_breakdown.items()
            },
            "payment_bill_count": payment_bill_count,
            "top_products": top_products,
        }

    except ValueError as e:

        return {
            "success": False,
            "message": str(e)
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error generating sales summary: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# DAILY SALES
# =========================================================

def get_daily_sales(
    sales_date=None
):
    """
    Return today's or specified day's sales.
    """

    if sales_date is None:
        sales_date = date.today()

    result = get_sales_summary(
        start_date=sales_date,
        end_date=sales_date
    )

    if result["success"]:

        result["message"] = (
            f"Sales for {result['start_date']}: "
            f"₹{result['total_sales']:.2f} "
            f"across {result['bill_count']} finalized bills."
        )

    return result


# =========================================================
# DAILY CLOSE
# =========================================================

def get_daily_close(
    close_date=None
):
    """
    Generate the operational daily-close summary.

    This is a reporting operation.
    It does not modify bills or stock.
    """

    if close_date is None:
        close_date = date.today()

    result = get_sales_summary(
        start_date=close_date,
        end_date=close_date
    )

    if not result["success"]:
        return result

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # INVENTORY SNAPSHOT
        # -------------------------------------------------

        products = (
            db.query(Product)
            .order_by(Product.name)
            .all()
        )

        total_products = len(products)

        low_stock_products = []

        out_of_stock_products = []

        total_stock_units = Decimal("0.00")

        for product in products:

            quantity = money(
                product.quantity
            )

            reorder_level = money(
                product.reorder_level
            )

            total_stock_units += quantity

            if quantity <= 0:

                out_of_stock_products.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "quantity": float(quantity),
                        "reorder_level": float(
                            reorder_level
                        )
                    }
                )

            elif quantity <= reorder_level:

                low_stock_products.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "sku": product.sku,
                        "quantity": float(quantity),
                        "reorder_level": float(
                            reorder_level
                        )
                    }
                )

        # -------------------------------------------------
        # PAYMENT MIX
        # -------------------------------------------------

        payments = result[
            "payment_breakdown"
        ]

        total_sales = money(
            result["total_sales"]
        )

        def percentage(value):

            if total_sales <= 0:
                return 0.0

            return float(
                (
                    money(value)
                    / total_sales
                    * Decimal("100")
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )

        payment_percentages = {
            key: percentage(value)
            for key, value in payments.items()
        }

        # -------------------------------------------------
        # TOP PRODUCT
        # -------------------------------------------------

        top_products = result[
            "top_products"
        ]

        top_product = None

        if top_products:

            top_product = top_products[0]

        # -------------------------------------------------
        # DAILY CLOSE STATUS
        # -------------------------------------------------

        if result["bill_count"] == 0:

            close_status = "no_sales"

        elif result["total_sales"] > 0:

            close_status = "ready"

        else:

            close_status = "ready"

        return {
            "success": True,
            "close_date": str(
                result["start_date"]
            ),
            "close_status": close_status,

            "sales": {
                "bill_count": result["bill_count"],
                "subtotal": result["subtotal"],
                "gst_collected": result["gst_collected"],
                "total_sales": result["total_sales"],
                "average_bill": result["average_bill"],
            },

            "payments": {
                "amounts": payments,
                "percentages": payment_percentages,
                "bill_counts": result[
                    "payment_bill_count"
                ],
            },

            "top_products": top_products,

            "inventory": {
                "total_products": total_products,
                "total_stock_units": float(
                    total_stock_units
                ),
                "low_stock_count": len(
                    low_stock_products
                ),
                "out_of_stock_count": len(
                    out_of_stock_products
                ),
                "low_stock_products": low_stock_products,
                "out_of_stock_products": (
                    out_of_stock_products
                ),
            },

            "top_product": top_product,

            "message": (
                f"Daily close for {result['start_date']}: "
                f"₹{result['total_sales']:.2f} sales, "
                f"₹{result['gst_collected']:.2f} GST, "
                f"{result['bill_count']} bills."
            ),
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error generating daily close: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# BUSINESS HEALTH SUMMARY
# =========================================================

def get_business_health(
    start_date=None,
    end_date=None
):
    """
    Generate a high-level operational health report.
    """

    sales = get_sales_summary(
        start_date,
        end_date
    )

    if not sales["success"]:
        return sales

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .all()
        )

        total_products = len(products)

        low_stock = []

        out_of_stock = []

        inventory_value = Decimal("0.00")

        for product in products:

            quantity = money(
                product.quantity
            )

            cost = money(
                product.cost_price
            )

            inventory_value += (
                quantity * cost
            )

            if quantity <= 0:

                out_of_stock.append(
                    product.name
                )

            elif quantity <= money(
                product.reorder_level
            ):

                low_stock.append(
                    product.name
                )

        # -------------------------------------------------
        # HEALTH SCORE
        # -------------------------------------------------

        score = 100

        if sales["bill_count"] == 0:
            score -= 20

        if len(low_stock) > 0:
            score -= min(
                20,
                len(low_stock) * 3
            )

        if len(out_of_stock) > 0:
            score -= min(
                30,
                len(out_of_stock) * 5
            )

        score = max(
            0,
            score
        )

        if score >= 80:
            health = "healthy"

        elif score >= 60:
            health = "attention_needed"

        else:
            health = "critical"

        recommendations = []

        if out_of_stock:

            recommendations.append(
                "Restock out-of-stock products."
            )

        if low_stock:

            recommendations.append(
                "Review low-stock products and reorder them."
            )

        if sales["bill_count"] == 0:

            recommendations.append(
                "No finalized sales were recorded for this period."
            )

        if not recommendations:

            recommendations.append(
                "Store operations look healthy for this period."
            )

        return {
            "success": True,

            "period": {
                "start_date": sales["start_date"],
                "end_date": sales["end_date"],
            },

            "sales": sales,

            "inventory": {
                "total_products": total_products,
                "low_stock_count": len(low_stock),
                "out_of_stock_count": len(out_of_stock),
                "low_stock_products": low_stock,
                "out_of_stock_products": out_of_stock,
                "inventory_cost_value": float(
                    money(inventory_value)
                ),
            },

            "health_score": score,

            "health_status": health,

            "recommendations": recommendations,
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error generating business health: {str(e)}"
            )
        }

    finally:

        db.close()