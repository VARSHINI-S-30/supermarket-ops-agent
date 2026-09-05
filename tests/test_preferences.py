from app.database.db import (
    engine,
    Base
)

from app.database.models import OwnerPreference

from app.tools.preferences import (
    set_preference,
    get_preference,
    get_preferences,
    clear_preference
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


print("=" * 60)
print("STEP 15 - PERSISTENT PREFERENCE TEST")
print("=" * 60)


# ============================================================
# CLEAN TEST PREFERENCES
# ============================================================

from app.database.db import SessionLocal

db = SessionLocal()

try:

    db.query(
        OwnerPreference
    ).delete()

    db.commit()

finally:

    db.close()


# ============================================================
# TEST 1
# SET DEFAULT PAYMENT
# ============================================================

print("\n--- TEST 1: SET DEFAULT PAYMENT ---")

result = set_preference(
    "default_payment",
    "upi"
)

print(result)

assert result["success"] is True

assert (
    result["preference_value"]
    == "upi"
)

print(
    "Default payment preference saved."
)


# ============================================================
# TEST 2
# GET DEFAULT PAYMENT
# ============================================================

print("\n--- TEST 2: GET DEFAULT PAYMENT ---")

result = get_preference(
    "default_payment"
)

print(result)

assert result["success"] is True

assert result["found"] is True

assert (
    result["preference_value"]
    == "upi"
)

print(
    "Preference retrieval passed."
)


# ============================================================
# TEST 3
# SET BRAND
# ============================================================

print("\n--- TEST 3: SET PREFERRED BRAND ---")

result = set_preference(
    "preferred_brand",
    "Aashirvaad"
)

print(result)

assert result["success"] is True

print(
    "Preferred brand saved."
)


# ============================================================
# TEST 4
# SET SHOP NAME
# ============================================================

print("\n--- TEST 4: SET SHOP NAME ---")

result = set_preference(
    "shop_name",
    "Sri Lakshmi Supermarket"
)

print(result)

assert result["success"] is True

print(
    "Shop name saved."
)


# ============================================================
# TEST 5
# SET GSTIN
# ============================================================

print("\n--- TEST 5: SET GSTIN ---")

result = set_preference(
    "gstin",
    "33ABCDE1234F1Z5"
)

print(result)

assert result["success"] is True

print(
    "GSTIN saved."
)


# ============================================================
# TEST 6
# GET ALL
# ============================================================

print("\n--- TEST 6: GET ALL PREFERENCES ---")

result = get_preferences()

print(result)

assert result["success"] is True

assert result["count"] == 4

assert (
    result["preferences"]["default_payment"]
    == "upi"
)

assert (
    result["preferences"]["preferred_brand"]
    == "Aashirvaad"
)

assert (
    result["preferences"]["shop_name"]
    == "Sri Lakshmi Supermarket"
)

assert (
    result["preferences"]["gstin"]
    == "33ABCDE1234F1Z5"
)

print(
    "All preferences retrieved correctly."
)


# ============================================================
# TEST 7
# UPDATE
# ============================================================

print("\n--- TEST 7: UPDATE PREFERENCE ---")

result = set_preference(
    "default_payment",
    "cash"
)

print(result)

assert result["success"] is True

result = get_preference(
    "default_payment"
)

print(result)

assert (
    result["preference_value"]
    == "cash"
)

print(
    "Preference update passed."
)


# ============================================================
# TEST 8
# INVALID PAYMENT
# ============================================================

print("\n--- TEST 8: INVALID PAYMENT ---")

result = set_preference(
    "default_payment",
    "bitcoin"
)

print(result)

assert result["success"] is False

print(
    "Invalid payment guard passed."
)


# ============================================================
# TEST 9
# INVALID GSTIN
# ============================================================

print("\n--- TEST 9: INVALID GSTIN ---")

result = set_preference(
    "gstin",
    "123"
)

print(result)

assert result["success"] is False

print(
    "GSTIN validation passed."
)


# ============================================================
# TEST 10
# CLEAR
# ============================================================

print("\n--- TEST 10: CLEAR PREFERENCE ---")

result = clear_preference(
    "preferred_brand"
)

print(result)

assert result["success"] is True

result = get_preference(
    "preferred_brand"
)

print(result)

assert result["found"] is False

print(
    "Preference clearing passed."
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 60)
print("STEP 15 PREFERENCE TEST COMPLETED SUCCESSFULLY")
print("=" * 60)