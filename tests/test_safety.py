from app.database.db import (
    SessionLocal,
    engine,
    Base
)

from app.database.models import (
    Product,
    Bill
)

from app.tools.inventory import (
    add_product,
    receive_stock
)

from app.tools.billing import (
    create_bill,
    add_item_to_bill,
    finalize_bill,
    get_bill
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


print("=" * 60)
print("STEP 14 - SAFETY / IDEMPOTENCY TEST")
print("=" * 60)


# ============================================================
# TEST PRODUCT
# ============================================================

TEST_SKU = "STEP14TEST"

db = SessionLocal()

try:

    existing = (
        db.query(Product)
        .filter(
            Product.sku == TEST_SKU
        )
        .first()
    )

    if existing:

        # Remove only the temporary test product.
        db.delete(existing)
        db.commit()

finally:

    db.close()


# ============================================================
# TEST 1
# SELLING BELOW COST
# ============================================================

print("\n--- TEST 1: SELLING BELOW COST ---")

result = add_product(
    name="Step14 Test Product",
    sku=TEST_SKU,
    unit="piece",
    cost_price=100,
    selling_price=90,
    mrp=120,
    quantity=10,
    reorder_level=2,
    gst_rate=12,
    hsn_code="9999"
)

print(result)

assert result["success"] is False

assert "below cost" in result["message"].lower()

print(
    "Selling-below-cost guard passed."
)


# ============================================================
# TEST 2
# VALID PRODUCT
# ============================================================

print("\n--- TEST 2: ADD VALID PRODUCT ---")

result = add_product(
    name="Step14 Test Product",
    sku=TEST_SKU,
    unit="piece",
    cost_price=100,
    selling_price=110,
    mrp=120,
    quantity=5,
    reorder_level=2,
    gst_rate=12,
    hsn_code="9999"
)

print(result)

assert result["success"] is True

print(
    "Valid product creation passed."
)


# ============================================================
# TEST 3
# MRP GUARD
# ============================================================

print("\n--- TEST 3: INVALID MRP ---")

result = receive_stock(
    sku=TEST_SKU,
    quantity=1,
    mrp=105
)

print(result)

assert result["success"] is False

print(
    "MRP guard passed."
)


# ============================================================
# TEST 4
# CREATE BILL
# ============================================================

print("\n--- TEST 4: CREATE BILL ---")

bill_result = create_bill()

print(bill_result)

assert bill_result["success"] is True

bill_id = bill_result["bill_id"]

print(
    f"Created test bill: {bill_id}"
)


# ============================================================
# TEST 5
# ADD ITEM
# ============================================================

print("\n--- TEST 5: ADD ITEM ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku=TEST_SKU,
    quantity=2
)

print(result)

assert result["success"] is True

print(
    "Bill item addition passed."
)


# ============================================================
# TEST 6
# GST BREAKUP
# ============================================================

print("\n--- TEST 6: GST BREAKUP ---")

bill = get_bill(
    bill_id
)

print(bill)

assert bill["success"] is True

assert "cgst_amount" in bill

assert "sgst_amount" in bill

assert round(
    bill["cgst_amount"]
    + bill["sgst_amount"],
    2
) == round(
    bill["gst_amount"],
    2
)

print(
    "CGST/SGST breakup passed."
)


# ============================================================
# TEST 7
# FINALIZE
# ============================================================

print("\n--- TEST 7: FINALIZE BILL ---")

result = finalize_bill(
    bill_id=bill_id,
    payment_mode="upi"
)

print(result)

assert result["success"] is True

assert result["idempotent"] is False

print(
    "First finalization passed."
)


# ============================================================
# CHECK STOCK
# ============================================================

db = SessionLocal()

try:

    product = (
        db.query(Product)
        .filter(
            Product.sku == TEST_SKU
        )
        .first()
    )

    stock_after_first_finalize = (
        product.quantity
    )

    print(
        "\nStock after first finalize:",
        stock_after_first_finalize
    )

finally:

    db.close()


# ============================================================
# TEST 8
# IDEMPOTENT RETRY
# ============================================================

print("\n--- TEST 8: IDEMPOTENT RETRY ---")

result = finalize_bill(
    bill_id=bill_id,
    payment_mode="upi"
)

print(result)

assert result["success"] is True

assert result["idempotent"] is True

print(
    "Idempotent finalize passed."
)


# ============================================================
# CHECK STOCK AGAIN
# ============================================================

db = SessionLocal()

try:

    product = (
        db.query(Product)
        .filter(
            Product.sku == TEST_SKU
        )
        .first()
    )

    stock_after_retry = (
        product.quantity
    )

    print(
        "Stock after retry:",
        stock_after_retry
    )

    assert (
        stock_after_retry
        == stock_after_first_finalize
    )

finally:

    db.close()


print(
    "Stock was not deducted twice."
)


# ============================================================
# TEST 9
# BILL STATUS
# ============================================================

print("\n--- TEST 9: FINAL BILL STATUS ---")

bill = get_bill(
    bill_id
)

print(bill)

assert bill["status"] == "finalized"

print(
    "Finalized bill status passed."
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 60)
print("STEP 14 SAFETY TEST COMPLETED SUCCESSFULLY")
print("=" * 60)