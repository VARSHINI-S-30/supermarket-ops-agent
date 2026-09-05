from app.database.db import Base, engine
from app.database.models import Product

from app.tools.preferences import (
    set_preference,
    get_preference,
    clear_preference
)

from app.tools.billing import (
    create_bill,
    add_item_to_bill,
    finalize_bill,
    get_bill
)

from app.services.invoice import generate_invoice


print("=" * 60)
print("STEP 19 TEST")
print("Preference-Aware Billing + Branded Invoice")
print("=" * 60)


# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

Base.metadata.create_all(
    bind=engine
)


# ----------------------------------------------------------
# CLEAN TEST PREFERENCES
# ----------------------------------------------------------

print("\n1. Clearing old test preferences...")

for key in [
    "default_payment",
    "shop_name",
    "gstin"
]:

    clear_preference(key)

print("Old preferences cleared.")


# ----------------------------------------------------------
# SAVE DEFAULT PAYMENT
# ----------------------------------------------------------

print("\n2. Setting default payment to UPI...")

result = set_preference(
    "default_payment",
    "upi"
)

print(result)

assert result["success"] is True
assert result["preference_value"] == "upi"


# ----------------------------------------------------------
# VERIFY DEFAULT PAYMENT
# ----------------------------------------------------------

print("\n3. Reading default payment...")

result = get_preference(
    "default_payment"
)

print(result)

assert result["success"] is True
assert result["found"] is True
assert result["preference_value"] == "upi"


# ----------------------------------------------------------
# SAVE SHOP NAME
# ----------------------------------------------------------

print("\n4. Saving shop name...")

result = set_preference(
    "shop_name",
    "Sri Lakshmi Supermarket"
)

print(result)

assert result["success"] is True


# ----------------------------------------------------------
# SAVE GSTIN
# ----------------------------------------------------------

print("\n5. Saving GSTIN...")

result = set_preference(
    "gstin",
    "33ABCDE1234F1Z5"
)

print(result)

assert result["success"] is True


# ----------------------------------------------------------
# FIND TEST PRODUCT
# ----------------------------------------------------------

from app.database.db import SessionLocal

db = SessionLocal()

try:

    product = (
        db.query(Product)
        .filter(Product.quantity > 0)
        .first()
    )

    if not product:

        print(
            "\nNo product with stock available."
        )

        print(
            "Add/receive stock and run the test again."
        )

        raise SystemExit(0)

    product_id = product.id
    product_name = product.name

finally:

    db.close()


print(
    f"\n6. Using test product: "
    f"{product_name} (ID {product_id})"
)


# ----------------------------------------------------------
# CREATE BILL
# ----------------------------------------------------------

print("\n7. Creating draft bill...")

result = create_bill()

print(result)

assert result["success"] is True

bill_id = result["bill_id"]

print(
    f"Created bill #{bill_id}"
)


# ----------------------------------------------------------
# ADD ITEM
# ----------------------------------------------------------

print("\n8. Adding one item...")

result = add_item_to_bill(
    bill_id=bill_id,
    product_id=product_id,
    quantity=1
)

print(result)

assert result["success"] is True


# ----------------------------------------------------------
# FINALIZE WITHOUT PAYMENT MODE
# ----------------------------------------------------------

print(
    "\n9. Finalizing WITHOUT specifying payment mode..."
)

result = finalize_bill(
    bill_id=bill_id
)

print(result)

assert result["success"] is True
assert result["idempotent"] is False
assert result["payment_mode"] == "upi"


print(
    "\nPASS: Saved default payment "
    "was automatically used."
)


# ----------------------------------------------------------
# VERIFY BILL
# ----------------------------------------------------------

print("\n10. Reading finalized bill...")

result = get_bill(
    bill_id
)

print(result)

assert result["success"] is True
assert result["status"] == "finalized"
assert result["payment_mode"] == "upi"


# ----------------------------------------------------------
# IDEMPOTENCY
# ----------------------------------------------------------

print(
    "\n11. Testing finalize idempotency..."
)

result = finalize_bill(
    bill_id=bill_id
)

print(result)

assert result["success"] is True
assert result["idempotent"] is True


print(
    "\nPASS: Retried finalize did not "
    "double-bill."
)


# ----------------------------------------------------------
# GENERATE INVOICE
# ----------------------------------------------------------

print(
    "\n12. Generating branded invoice..."
)

result = generate_invoice(
    bill_id
)

print(result)

assert result["success"] is True
assert result["shop_name"] == (
    "Sri Lakshmi Supermarket"
)
assert result["gstin"] == (
    "33ABCDE1234F1Z5"
)


print(
    "\nPASS: Invoice uses persistent "
    "shop name and GSTIN."
)


# ----------------------------------------------------------
# COMPLETE
# ----------------------------------------------------------

print("\n" + "=" * 60)
print("STEP 19 COMPLETED SUCCESSFULLY")
print("=" * 60)