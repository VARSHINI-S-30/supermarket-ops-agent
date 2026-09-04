import os

from app.services.invoice import generate_invoice


print("\n========================================")
print("STEP 7 - PDF INVOICE TEST")
print("========================================")


# ============================================================
# TEST 1 - GENERATE EXISTING FINALIZED BILL
# ============================================================

print("\n--- TEST 1: FINALIZED BILL ---")

result = generate_invoice(9)

print(result)

if result["success"]:

    filepath = result["filepath"]

    print(
        f"PDF exists: {os.path.exists(filepath)}"
    )

    if os.path.exists(filepath):

        print(
            f"PDF size: "
            f"{os.path.getsize(filepath)} bytes"
        )


# ============================================================
# TEST 2 - INVALID BILL
# ============================================================

print("\n--- TEST 2: INVALID BILL ---")

result = generate_invoice(99999)

print(result)


# ============================================================
# TEST 3 - DRAFT BILL
# ============================================================

print("\n--- TEST 3: DRAFT BILL ---")

from app.tools.billing import create_bill

draft_bill = create_bill()

print(draft_bill)

if draft_bill["success"]:

    draft_bill_id = draft_bill["bill_id"]

    result = generate_invoice(
        draft_bill_id
    )

    print(result)


# ============================================================
# FINAL
# ============================================================

print("\n========================================")
print("STEP 7 TEST COMPLETED")
print("========================================")