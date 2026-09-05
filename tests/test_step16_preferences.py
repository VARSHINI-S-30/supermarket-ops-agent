from app.database.db import Base, engine
from app.database.models import (
    OwnerPreference,
    Bill
)

from app.tools.preferences import (
    set_preference,
    get_preference,
    clear_preference,
    get_preferences,
)

from app.services.invoice import (
    get_invoice_preferences
)


print("=" * 60)
print("STEP 16 - PREFERENCE OPERATIONAL TEST")
print("=" * 60)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

Base.metadata.create_all(
    bind=engine
)

print("\n1. Database ready.")


# ---------------------------------------------------------
# CLEAR OLD TEST VALUES
# ---------------------------------------------------------

for key in [
    "default_payment",
    "shop_name",
    "gstin",
]:
    result = clear_preference(key)

    print(
        f"Clearing {key}:",
        result
    )


# ---------------------------------------------------------
# TEST DEFAULT PAYMENT
# ---------------------------------------------------------

result = set_preference(
    "default_payment",
    "upi"
)

print(
    "\n2. Set default payment:",
    result
)

assert result["success"] is True

result = get_preference(
    "default_payment"
)

print(
    "Retrieved default payment:",
    result
)

assert result["success"] is True
assert result["found"] is True
assert result["preference_value"] == "upi"


# ---------------------------------------------------------
# TEST SHOP NAME
# ---------------------------------------------------------

result = set_preference(
    "shop_name",
    "Sri Lakshmi Supermarket"
)

print(
    "\n3. Set shop name:",
    result
)

assert result["success"] is True


# ---------------------------------------------------------
# TEST GSTIN
# ---------------------------------------------------------

result = set_preference(
    "gstin",
    "33ABCDE1234F1Z5"
)

print(
    "\n4. Set GSTIN:",
    result
)

assert result["success"] is True


# ---------------------------------------------------------
# TEST INVOICE PREFERENCES
# ---------------------------------------------------------

invoice_preferences = get_invoice_preferences()

print(
    "\n5. Invoice preferences:"
)

print(
    invoice_preferences
)

assert (
    invoice_preferences["shop_name"]
    == "Sri Lakshmi Supermarket"
)

assert (
    invoice_preferences["gstin"]
    == "33ABCDE1234F1Z5"
)


# ---------------------------------------------------------
# TEST ALL PREFERENCES
# ---------------------------------------------------------

result = get_preferences()

print(
    "\n6. All preferences:"
)

print(
    result
)

assert result["success"] is True

assert (
    result["preferences"]["default_payment"]
    == "upi"
)

assert (
    result["preferences"]["shop_name"]
    == "Sri Lakshmi Supermarket"
)

assert (
    result["preferences"]["gstin"]
    == "33ABCDE1234F1Z5"
)


# ---------------------------------------------------------
# TEST INVALID PAYMENT
# ---------------------------------------------------------

result = set_preference(
    "default_payment",
    "bitcoin"
)

print(
    "\n7. Invalid payment test:"
)

print(
    result
)

assert result["success"] is False


# ---------------------------------------------------------
# TEST INVALID GSTIN
# ---------------------------------------------------------

result = set_preference(
    "gstin",
    "123"
)

print(
    "\n8. Invalid GSTIN test:"
)

print(
    result
)

assert result["success"] is False


# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("STEP 16 BASIC TESTS PASSED SUCCESSFULLY")
print("=" * 60)