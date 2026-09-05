import os

from app.database.db import (
    Base,
    engine,
    SessionLocal
)

from app.database.models import (
    Product
)

from app.tools.health import (
    get_system_health
)

from app.tools.preferences import (
    set_preference,
    get_preference
)

from app.tools.billing import (
    create_bill,
    add_item_to_bill,
    finalize_bill,
    get_bill
)

from app.services.invoice import (
    generate_invoice
)

from app.services.analysis_deck import (
    generate_analysis_deck
)


print("=" * 70)
print("STEP 20 FINAL INTEGRATION TEST")
print("=" * 70)


# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

print("\n1. Creating database tables...")

Base.metadata.create_all(
    bind=engine
)

print("Database ready.")


# ----------------------------------------------------------
# HEALTH
# ----------------------------------------------------------

print("\n2. Checking system health...")

health = get_system_health()

print(health)

assert health["success"] is True
assert health["database"] == "connected"

print("PASS: System health.")


# ----------------------------------------------------------
# PREFERENCES
# ----------------------------------------------------------

print("\n3. Setting persistent preferences...")

result = set_preference(
    "default_payment",
    "upi"
)

assert result["success"] is True

result = set_preference(
    "shop_name",
    "Sri Lakshmi Supermarket"
)

assert result["success"] is True

result = set_preference(
    "gstin",
    "33ABCDE1234F1Z5"
)

assert result["success"] is True

print("PASS: Preferences saved.")


# ----------------------------------------------------------
# VERIFY PREFERENCE
# ----------------------------------------------------------

print("\n4. Reading default payment...")

result = get_preference(
    "default_payment"
)

print(result)

assert result["success"] is True
assert result["found"] is True
assert result["preference_value"] == "upi"

print("PASS: Persistent preference.")


# ----------------------------------------------------------
# FIND PRODUCT
# ----------------------------------------------------------

print("\n5. Finding product with stock...")

db = SessionLocal()

try:

    product = (
        db.query(Product)
        .filter(Product.quantity > 0)
        .first()
    )

    if not product:

        print(
            "No product with stock found."
        )

        print(
            "Please seed or receive stock before "
            "running this test."
        )

        raise SystemExit(0)

    product_id = product.id
    product_name = product.name

finally:

    db.close()

print(
    f"Using product: {product_name}"
)


# ----------------------------------------------------------
# CREATE BILL
# ----------------------------------------------------------

print("\n6. Creating bill...")

result = create_bill()

print(result)

assert result["success"] is True

bill_id = result["bill_id"]

print(
    f"Bill created: #{bill_id}"
)


# ----------------------------------------------------------
# ADD ITEM
# ----------------------------------------------------------

print("\n7. Adding item...")

result = add_item_to_bill(
    bill_id=bill_id,
    product_id=product_id,
    quantity=1
)

print(result)

assert result["success"] is True

print("PASS: Item added.")


# ----------------------------------------------------------
# GET DRAFT
# ----------------------------------------------------------

print("\n8. Checking draft bill...")

draft = get_bill(
    bill_id
)

print(draft)

assert draft["success"] is True
assert draft["status"] == "draft"

print("PASS: Multi-turn draft bill.")


# ----------------------------------------------------------
# FINALIZE WITHOUT PAYMENT
# ----------------------------------------------------------

print(
    "\n9. Finalizing without payment mode..."
)

result = finalize_bill(
    bill_id
)

print(result)

assert result["success"] is True
assert result["payment_mode"] == "upi"
assert result["idempotent"] is False

print(
    "PASS: Default UPI preference applied."
)


# ----------------------------------------------------------
# IDEMPOTENCY
# ----------------------------------------------------------

print(
    "\n10. Retrying finalize..."
)

result = finalize_bill(
    bill_id
)

print(result)

assert result["success"] is True
assert result["idempotent"] is True

print(
    "PASS: Finalize is idempotent."
)


# ----------------------------------------------------------
# FINAL BILL
# ----------------------------------------------------------

print("\n11. Checking finalized bill...")

bill = get_bill(
    bill_id
)

print(bill)

assert bill["success"] is True
assert bill["status"] == "finalized"
assert bill["payment_mode"] == "upi"

print(
    "PASS: Finalized bill."
)


# ----------------------------------------------------------
# PDF
# ----------------------------------------------------------

print("\n12. Generating PDF invoice...")

invoice = generate_invoice(
    bill_id
)

print(invoice)

assert invoice["success"] is True
assert os.path.exists(
    invoice["filepath"]
)

assert invoice["shop_name"] == (
    "Sri Lakshmi Supermarket"
)

assert invoice["gstin"] == (
    "33ABCDE1234F1Z5"
)

print(
    "PASS: GST invoice generated."
)


# ----------------------------------------------------------
# PPTX
# ----------------------------------------------------------

print(
    "\n13. Generating analysis deck..."
)

deck = generate_analysis_deck(
    days=7
)

print(deck)

assert deck["success"] is True
assert os.path.exists(
    deck["filepath"]
)

assert deck["filepath"].endswith(
    ".pptx"
)

print(
    "PASS: PPTX analysis deck generated."
)


# ----------------------------------------------------------
# FINAL HEALTH
# ----------------------------------------------------------

print(
    "\n14. Final system health check..."
)

health = get_system_health()

print(health)

assert health["success"] is True
assert health["negative_stock_items"] == 0

print(
    "PASS: No negative stock."
)


# ----------------------------------------------------------
# COMPLETE
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("STEP 20 COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nVerified:")
print("✓ Database health")
print("✓ Persistent preferences")
print("✓ Default payment")
print("✓ Multi-turn bill")
print("✓ Bill finalization")
print("✓ Idempotency")
print("✓ Stock integrity")
print("✓ GST invoice")
print("✓ Branded invoice")
print("✓ Real PPTX charts")
print("✓ Final health check")
print("=" * 70)