from app.database.db import SessionLocal
from app.database.models import Customer


def get_customer_credit(customer_id):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": (
                    f"Customer with ID {customer_id} not found."
                )
            }

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "credit_balance": customer.credit_balance
        }

    finally:
        db.close()


def record_credit_payment(customer_id, amount):
    db = SessionLocal()

    try:
        if amount <= 0:
            return {
                "success": False,
                "message": "Payment amount must be greater than zero."
            }

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": (
                    f"Customer with ID {customer_id} not found."
                )
            }

        if amount > customer.credit_balance:
            return {
                "success": False,
                "message": (
                    f"Payment exceeds outstanding credit. "
                    f"Current balance: ₹{customer.credit_balance:.2f}"
                )
            }

        old_balance = customer.credit_balance

        customer.credit_balance -= amount

        db.commit()
        db.refresh(customer)

        return {
            "success": True,
            "message": "Credit payment recorded successfully.",
            "customer_id": customer.id,
            "customer_name": customer.name,
            "previous_balance": old_balance,
            "payment": amount,
            "remaining_balance": customer.credit_balance
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": f"Error recording payment: {str(e)}"
        }

    finally:
        db.close()