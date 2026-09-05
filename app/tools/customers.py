from decimal import Decimal, ROUND_HALF_UP

from app.database.db import (
    SessionLocal,
    begin_write_transaction
)

from app.database.models import Customer


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


# =========================================================
# ADD CUSTOMER
# =========================================================

def add_customer(
    name,
    phone=None
):
    """
    Create a new supermarket customer.

    A customer starts with zero credit balance.
    """

    db = SessionLocal()

    try:

        if not name:

            return {
                "success": False,
                "message": "Customer name cannot be empty."
            }

        name = str(name).strip()

        if not name:

            return {
                "success": False,
                "message": "Customer name cannot be empty."
            }

        if phone is not None:

            phone = str(phone).strip()

            if not phone:

                phone = None

        begin_write_transaction(db)

        # -------------------------------------------------
        # CHECK DUPLICATE PHONE
        # -------------------------------------------------

        if phone:

            existing = (
                db.query(Customer)
                .filter(
                    Customer.phone == phone
                )
                .first()
            )

            if existing:

                return {
                    "success": False,
                    "message": (
                        f"A customer with phone "
                        f"{phone} already exists."
                    ),
                    "customer_id": existing.id,
                    "customer_name": existing.name
                }

        # -------------------------------------------------
        # CREATE CUSTOMER
        # -------------------------------------------------

        customer = Customer(
            name=name,
            phone=phone,
            credit_balance=0
        )

        db.add(customer)

        db.commit()

        db.refresh(customer)

        return {
            "success": True,
            "message": (
                f"Customer '{customer.name}' "
                "created successfully."
            ),
            "customer_id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "credit_balance": 0.0
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error creating customer: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# SEARCH CUSTOMERS
# =========================================================

def search_customers(
    query
):
    """
    Search customers by name or phone.
    """

    db = SessionLocal()

    try:

        if not query:

            return {
                "success": False,
                "message": "Search query cannot be empty."
            }

        query = str(query).strip()

        if not query:

            return {
                "success": False,
                "message": "Search query cannot be empty."
            }

        pattern = f"%{query}%"

        customers = (
            db.query(Customer)
            .filter(
                (
                    Customer.name.ilike(pattern)
                )
                |
                (
                    Customer.phone.ilike(pattern)
                )
            )
            .order_by(
                Customer.name
            )
            .all()
        )

        results = []

        for customer in customers:

            results.append(
                {
                    "customer_id": customer.id,
                    "name": customer.name,
                    "phone": customer.phone,
                    "credit_balance": float(
                        money(
                            customer.credit_balance
                        )
                    )
                }
            )

        return {
            "success": True,
            "count": len(results),
            "customers": results
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error searching customers: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# GET CUSTOMER
# =========================================================

def get_customer(
    customer_id
):
    """
    Retrieve one customer and their current credit balance.
    """

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
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

        return {
            "success": True,
            "customer": {
                "customer_id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "credit_balance": float(
                    money(
                        customer.credit_balance
                    )
                )
            }
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error retrieving customer: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# GET CUSTOMER CREDIT
# =========================================================

def get_customer_credit(
    customer_id
):
    """
    Return the customer's current outstanding credit.
    """

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
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

        balance = money(
            customer.credit_balance
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "phone": customer.phone,
            "credit_balance": float(balance),
            "message": (
                f"{customer.name} has outstanding "
                f"credit of ₹{balance:.2f}."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error retrieving credit: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# RECORD CREDIT PAYMENT
# =========================================================

def record_credit_payment(
    customer_id,
    amount
):
    """
    Record a payment against customer credit.

    Safety rules:

    - customer must exist
    - amount must be positive
    - payment cannot exceed outstanding credit
    - credit balance can never become negative
    """

    db = SessionLocal()

    try:

        if amount is None:

            return {
                "success": False,
                "message": "Payment amount is required."
            }

        try:

            payment = money(amount)

        except Exception:

            return {
                "success": False,
                "message": "Invalid payment amount."
            }

        if payment <= 0:

            return {
                "success": False,
                "message": (
                    "Payment amount must be greater than zero."
                )
            }

        begin_write_transaction(db)

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
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

        current_balance = money(
            customer.credit_balance
        )

        # -------------------------------------------------
        # PREVENT OVERPAYMENT
        # -------------------------------------------------

        if payment > current_balance:

            return {
                "success": False,
                "message": (
                    f"Payment of ₹{payment:.2f} exceeds "
                    f"the outstanding credit of "
                    f"₹{current_balance:.2f}."
                ),
                "customer_id": customer.id,
                "customer_name": customer.name,
                "credit_balance": float(
                    current_balance
                )
            }

        new_balance = (
            current_balance - payment
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -------------------------------------------------
        # SAFETY CHECK
        # -------------------------------------------------

        if new_balance < 0:

            return {
                "success": False,
                "message": (
                    "Credit balance cannot become negative."
                )
            }

        customer.credit_balance = float(
            new_balance
        )

        db.commit()

        return {
            "success": True,
            "message": (
                f"Payment of ₹{payment:.2f} recorded "
                f"for {customer.name}."
            ),
            "customer_id": customer.id,
            "customer_name": customer.name,
            "payment_amount": float(payment),
            "previous_balance": float(
                current_balance
            ),
            "remaining_balance": float(
                new_balance
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error recording credit payment: {str(e)}"
            )
        }

    finally:

        db.close()


# =========================================================
# CUSTOMER CREDIT SUMMARY
# =========================================================

def get_customer_credit_summary(
    customer_id
):
    """
    Return a simple customer credit summary.
    """

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == customer_id
            )
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

        balance = money(
            customer.credit_balance
        )

        if balance > 0:

            status = "outstanding"

        else:

            status = "settled"

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "phone": customer.phone,
            "credit_balance": float(balance),
            "status": status
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error generating credit summary: {str(e)}"
            )
        }

    finally:

        db.close()