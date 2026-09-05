from app.database.db import (
    Base,
    engine,
    SessionLocal
)

from app.database.models import Customer

from app.tools.customers import (
    add_customer,
    search_customers,
    get_customer,
    get_customer_credit,
    record_credit_payment,
    get_customer_credit_summary,
)


print("=" * 60)
print("STEP 17 - CUSTOMER / KHATA TEST")
print("=" * 60)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)

print("\n1. Database ready.")


# =========================================================
# CLEAN TEST CUSTOMER
# =========================================================

db = SessionLocal()

try:

    existing = (
        db.query(Customer)
        .filter(
            Customer.phone == "9999999999"
        )
        .first()
    )

    if existing:

        db.delete(existing)

        db.commit()

        print(
            "Old test customer removed."
        )

finally:

    db.close()


# =========================================================
# ADD CUSTOMER
# =========================================================

result = add_customer(
    name="Test Customer",
    phone="9999999999"
)

print(
    "\n2. Add customer:"
)

print(result)

assert result["success"] is True

customer_id = result["customer_id"]

print(
    f"Customer ID: {customer_id}"
)


# =========================================================
# SEARCH CUSTOMER
# =========================================================

result = search_customers(
    "Test Customer"
)

print(
    "\n3. Search customer:"
)

print(result)

assert result["success"] is True

assert result["count"] >= 1


# =========================================================
# GET CUSTOMER
# =========================================================

result = get_customer(
    customer_id
)

print(
    "\n4. Get customer:"
)

print(result)

assert result["success"] is True

assert (
    result["customer"]["name"]
    == "Test Customer"
)


# =========================================================
# INITIAL CREDIT
# =========================================================

result = get_customer_credit(
    customer_id
)

print(
    "\n5. Initial credit:"
)

print(result)

assert result["success"] is True

assert (
    result["credit_balance"]
    == 0.0
)


# =========================================================
# CREDIT SUMMARY
# =========================================================

result = get_customer_credit_summary(
    customer_id
)

print(
    "\n6. Credit summary:"
)

print(result)

assert result["success"] is True

assert (
    result["status"]
    == "settled"
)


# =========================================================
# CREATE CREDIT BALANCE DIRECTLY
# FOR TESTING PAYMENT SAFETY
# =========================================================

db = SessionLocal()

try:

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id
        )
        .first()
    )

    customer.credit_balance = 1000.00

    db.commit()

finally:

    db.close()


print(
    "\n7. Test credit balance set to ₹1000."
)


# =========================================================
# CHECK CREDIT
# =========================================================

result = get_customer_credit(
    customer_id
)

print(
    "\n8. Credit after test balance:"
)

print(result)

assert result["success"] is True

assert (
    result["credit_balance"]
    == 1000.0
)


# =========================================================
# VALID CREDIT PAYMENT
# =========================================================

result = record_credit_payment(
    customer_id,
    400
)

print(
    "\n9. Pay ₹400:"
)

print(result)

assert result["success"] is True

assert (
    result["remaining_balance"]
    == 600.0
)


# =========================================================
# CHECK REMAINING CREDIT
# =========================================================

result = get_customer_credit(
    customer_id
)

print(
    "\n10. Remaining credit:"
)

print(result)

assert result["success"] is True

assert (
    result["credit_balance"]
    == 600.0
)


# =========================================================
# OVERPAYMENT TEST
# =========================================================

result = record_credit_payment(
    customer_id,
    1000
)

print(
    "\n11. Overpayment test:"
)

print(result)

assert result["success"] is False


# =========================================================
# VERIFY BALANCE DID NOT CHANGE
# =========================================================

result = get_customer_credit(
    customer_id
)

print(
    "\n12. Credit after rejected overpayment:"
)

print(result)

assert result["success"] is True

assert (
    result["credit_balance"]
    == 600.0
)


# =========================================================
# ZERO PAYMENT TEST
# =========================================================

result = record_credit_payment(
    customer_id,
    0
)

print(
    "\n13. Zero payment test:"
)

print(result)

assert result["success"] is False


# =========================================================
# NEGATIVE PAYMENT TEST
# =========================================================

result = record_credit_payment(
    customer_id,
    -100
)

print(
    "\n14. Negative payment test:"
)

print(result)

assert result["success"] is False


# =========================================================
# UNKNOWN CUSTOMER TEST
# =========================================================

result = get_customer_credit(
    999999
)

print(
    "\n15. Unknown customer test:"
)

print(result)

assert result["success"] is False


# =========================================================
# DUPLICATE PHONE TEST
# =========================================================

result = add_customer(
    name="Another Customer",
    phone="9999999999"
)

print(
    "\n16. Duplicate phone test:"
)

print(result)

assert result["success"] is False


# =========================================================
# FINAL CREDIT SUMMARY
# =========================================================

result = get_customer_credit_summary(
    customer_id
)

print(
    "\n17. Final credit summary:"
)

print(result)

assert result["success"] is True

assert (
    result["credit_balance"]
    == 600.0
)

assert (
    result["status"]
    == "outstanding"
)


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 60)

print(
    "STEP 17 CUSTOMER / KHATA TESTS PASSED SUCCESSFULLY"
)

print("=" * 60)