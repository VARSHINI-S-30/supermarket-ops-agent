from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.database.db import SessionLocal
from app.database.models import Bill


# Store operates in India
STORE_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _safe_float(value):
    """
    Convert database numeric values safely to float.
    Prevents errors if an old record contains None.
    """
    if value is None:
        return 0.0

    return float(value)


def _round_money(value):
    """
    Round currency values to two decimal places.
    """
    return round(_safe_float(value), 2)


def _get_utc_boundaries_for_store_date(store_date):
    """
    The database currently stores Bill.created_at using datetime.utcnow(),
    which is a naive UTC datetime.

    This function converts an Indian calendar day into the matching
    UTC start/end timestamps so that 'today' means today in India.
    """

    local_start = datetime(
        year=store_date.year,
        month=store_date.month,
        day=store_date.day,
        hour=0,
        minute=0,
        second=0,
        tzinfo=STORE_TIMEZONE
    )

    local_end = local_start + timedelta(days=1)

    utc_start = (
        local_start
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )

    utc_end = (
        local_end
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )

    return utc_start, utc_end


def get_sales_summary(date=None):
    """
    Generate sales summary for a given Indian calendar date.

    Parameters
    ----------
    date:
        None
            -> today's date in India

        "YYYY-MM-DD"
            -> summary for the specified date

    Example
    -------
    get_sales_summary()

    get_sales_summary("2026-09-04")
    """

    db = SessionLocal()

    try:

        # ====================================================
        # DETERMINE DATE
        # ====================================================

        if date is None:

            current_time = datetime.now(STORE_TIMEZONE)
            store_date = current_time.date()

        elif isinstance(date, str):

            date = date.strip()

            if not date:
                return {
                    "success": False,
                    "message": (
                        "Date cannot be empty. "
                        "Use YYYY-MM-DD format."
                    )
                }

            try:
                store_date = datetime.strptime(
                    date,
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                return {
                    "success": False,
                    "message": (
                        "Invalid date format. "
                        "Use YYYY-MM-DD, for example 2026-09-04."
                    )
                }

        else:

            return {
                "success": False,
                "message": (
                    "Date must be provided as a string "
                    "in YYYY-MM-DD format."
                )
            }

        # ====================================================
        # CONVERT STORE DAY TO UTC DATABASE RANGE
        # ====================================================

        utc_start, utc_end = (
            _get_utc_boundaries_for_store_date(store_date)
        )

        # ====================================================
        # FETCH FINALIZED BILLS ONLY
        # ====================================================

        bills = (
            db.query(Bill)
            .filter(
                Bill.status == "finalized",
                Bill.created_at >= utc_start,
                Bill.created_at < utc_end
            )
            .order_by(Bill.created_at.asc())
            .all()
        )

        # ====================================================
        # INITIALIZE TOTALS
        # ====================================================

        subtotal = 0.0
        gst_amount = 0.0
        total_sales = 0.0

        cash_sales = 0.0
        upi_sales = 0.0
        card_sales = 0.0
        credit_sales = 0.0
        other_sales = 0.0

        cash_bills = 0
        upi_bills = 0
        card_bills = 0
        credit_bills = 0
        other_bills = 0

        # ====================================================
        # PROCESS EACH BILL
        # ====================================================

        bill_details = []

        for bill in bills:

            bill_subtotal = _safe_float(
                bill.subtotal
            )

            bill_gst = _safe_float(
                bill.gst_amount
            )

            bill_total = _safe_float(
                bill.total_amount
            )

            subtotal += bill_subtotal
            gst_amount += bill_gst
            total_sales += bill_total

            payment_mode = (
                bill.payment_mode.lower().strip()
                if bill.payment_mode
                else "unknown"
            )

            # --------------------------------------------
            # PAYMENT MODE BREAKDOWN
            # --------------------------------------------

            if payment_mode == "cash":

                cash_sales += bill_total
                cash_bills += 1

            elif payment_mode == "upi":

                upi_sales += bill_total
                upi_bills += 1

            elif payment_mode == "card":

                card_sales += bill_total
                card_bills += 1

            elif payment_mode == "credit":

                credit_sales += bill_total
                credit_bills += 1

            else:

                # Safety for old / unexpected data
                other_sales += bill_total
                other_bills += 1

            # --------------------------------------------
            # CONVERT BILL TIME TO STORE TIMEZONE
            # --------------------------------------------

            created_at_local = None

            if bill.created_at:

                # created_at in existing database is naive UTC
                created_at_utc = bill.created_at.replace(
                    tzinfo=timezone.utc
                )

                created_at_local = (
                    created_at_utc
                    .astimezone(STORE_TIMEZONE)
                    .isoformat()
                )

            bill_details.append({
                "bill_id": bill.id,
                "customer_id": bill.customer_id,
                "payment_mode": payment_mode,
                "subtotal": _round_money(
                    bill_subtotal
                ),
                "gst_amount": _round_money(
                    bill_gst
                ),
                "total_amount": _round_money(
                    bill_total
                ),
                "created_at": created_at_local
            })

        # ====================================================
        # NO SALES CASE
        # ====================================================

        if not bills:

            return {
                "success": True,
                "message": (
                    f"No finalized sales recorded "
                    f"for {store_date}."
                ),
                "date": str(store_date),
                "timezone": "Asia/Kolkata",
                "total_bills": 0,
                "subtotal": 0.0,
                "gst_amount": 0.0,
                "total_sales": 0.0,
                "average_bill_value": 0.0,

                "payment_summary": {
                    "cash": {
                        "bills": 0,
                        "amount": 0.0
                    },
                    "upi": {
                        "bills": 0,
                        "amount": 0.0
                    },
                    "card": {
                        "bills": 0,
                        "amount": 0.0
                    },
                    "credit": {
                        "bills": 0,
                        "amount": 0.0
                    },
                    "other": {
                        "bills": 0,
                        "amount": 0.0
                    }
                },

                "bills": []
            }

        # ====================================================
        # AVERAGE BILL VALUE
        # ====================================================

        average_bill_value = (
            total_sales / len(bills)
            if bills
            else 0.0
        )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {
            "success": True,
            "message": (
                "Daily sales summary generated successfully."
            ),
            "date": str(store_date),
            "timezone": "Asia/Kolkata",
            "total_bills": len(bills),

            "subtotal": _round_money(
                subtotal
            ),

            "gst_amount": _round_money(
                gst_amount
            ),

            "total_sales": _round_money(
                total_sales
            ),

            "average_bill_value": _round_money(
                average_bill_value
            ),

            "payment_summary": {

                "cash": {
                    "bills": cash_bills,
                    "amount": _round_money(
                        cash_sales
                    )
                },

                "upi": {
                    "bills": upi_bills,
                    "amount": _round_money(
                        upi_sales
                    )
                },

                "card": {
                    "bills": card_bills,
                    "amount": _round_money(
                        card_sales
                    )
                },

                "credit": {
                    "bills": credit_bills,
                    "amount": _round_money(
                        credit_sales
                    )
                },

                "other": {
                    "bills": other_bills,
                    "amount": _round_money(
                        other_sales
                    )
                }
            },

            "bills": bill_details
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


# ============================================================
# SIMPLE TODAY'S SALES FUNCTION
# ============================================================

def get_daily_sales():
    """
    Convenience function for the AI agent.

    Example user request:
    'How much did I sell today?'
    """

    return get_sales_summary()


# ============================================================
# DAILY CLOSE
# ============================================================

def get_daily_close(date=None):
    """
    Provides a shorter business-closing summary.

    This can later be used by Telegram for requests such as:
    'Close today's business'
    'Give me today's closing report'
    """

    result = get_sales_summary(date)

    if not result.get("success"):
        return result

    payment_summary = result["payment_summary"]

    received_amount = (
        payment_summary["cash"]["amount"]
        + payment_summary["upi"]["amount"]
        + payment_summary["card"]["amount"]
        + payment_summary["other"]["amount"]
    )

    credit_given = (
        payment_summary["credit"]["amount"]
    )

    return {
        "success": True,
        "message": (
            "Daily close generated successfully."
        ),
        "date": result["date"],
        "timezone": result["timezone"],
        "total_bills": result["total_bills"],
        "subtotal": result["subtotal"],
        "gst_amount": result["gst_amount"],
        "total_sales": result["total_sales"],
        "received_amount": _round_money(
            received_amount
        ),
        "credit_sales": _round_money(
            credit_given
        ),
        "average_bill_value": (
            result["average_bill_value"]
        ),
        "payment_summary": payment_summary
    }