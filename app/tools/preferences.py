from app.database.db import (
    SessionLocal,
    begin_write_transaction
)

from app.database.models import OwnerPreference


# ============================================================
# ALLOWED PREFERENCES
# ============================================================

ALLOWED_PREFERENCES = {
    "default_payment",
    "preferred_brand",
    "shop_name",
    "gstin"
}


# ============================================================
# SET PREFERENCE
# ============================================================

def set_preference(
    preference_key,
    preference_value
):

    db = SessionLocal()

    try:

        if not preference_key:
            return {
                "success": False,
                "message": "Preference key cannot be empty."
            }

        if not preference_value:
            return {
                "success": False,
                "message": "Preference value cannot be empty."
            }

        preference_key = (
            str(preference_key)
            .strip()
            .lower()
        )

        preference_value = (
            str(preference_value)
            .strip()
        )

        if preference_key not in ALLOWED_PREFERENCES:

            return {
                "success": False,
                "message": (
                    f"Unsupported preference '{preference_key}'. "
                    f"Allowed preferences: "
                    f"{', '.join(sorted(ALLOWED_PREFERENCES))}."
                )
            }

        # ----------------------------------------------------
        # Validate default payment
        # ----------------------------------------------------

        if preference_key == "default_payment":

            payment = preference_value.lower()

            allowed_payments = {
                "cash",
                "upi",
                "card",
                "credit"
            }

            if payment not in allowed_payments:

                return {
                    "success": False,
                    "message": (
                        "Invalid default payment. "
                        "Allowed values: cash, upi, card, credit."
                    )
                }

            preference_value = payment

        # ----------------------------------------------------
        # Validate GSTIN
        # ----------------------------------------------------

        if preference_key == "gstin":

            gstin = (
                preference_value
                .upper()
                .replace(" ", "")
            )

            if len(gstin) != 15:

                return {
                    "success": False,
                    "message": (
                        "GSTIN must contain exactly 15 characters."
                    )
                }

            preference_value = gstin

        # ----------------------------------------------------
        # Lock database before changing preference.
        # ----------------------------------------------------

        begin_write_transaction(db)

        existing = (
            db.query(OwnerPreference)
            .filter(
                OwnerPreference.preference_key
                == preference_key
            )
            .first()
        )

        if existing:

            existing.preference_value = preference_value

            action = "updated"

        else:

            preference = OwnerPreference(
                preference_key=preference_key,
                preference_value=preference_value
            )

            db.add(preference)

            action = "saved"

        db.commit()

        return {
            "success": True,
            "message": (
                f"Preference '{preference_key}' "
                f"{action} successfully."
            ),
            "preference_key": preference_key,
            "preference_value": preference_value
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error saving preference: {str(e)}"
            )
        }

    finally:

        db.close()


# ============================================================
# GET ONE PREFERENCE
# ============================================================

def get_preference(
    preference_key
):

    db = SessionLocal()

    try:

        if not preference_key:

            return {
                "success": False,
                "message": (
                    "Preference key cannot be empty."
                )
            }

        preference_key = (
            str(preference_key)
            .strip()
            .lower()
        )

        if preference_key not in ALLOWED_PREFERENCES:

            return {
                "success": False,
                "message": (
                    f"Unsupported preference "
                    f"'{preference_key}'."
                )
            }

        preference = (
            db.query(OwnerPreference)
            .filter(
                OwnerPreference.preference_key
                == preference_key
            )
            .first()
        )

        if not preference:

            return {
                "success": True,
                "found": False,
                "preference_key": preference_key,
                "preference_value": None,
                "message": (
                    "No value has been saved for "
                    f"'{preference_key}'."
                )
            }

        return {
            "success": True,
            "found": True,
            "preference_key": preference.preference_key,
            "preference_value": preference.preference_value
        }

    finally:

        db.close()


# ============================================================
# GET ALL PREFERENCES
# ============================================================

def get_preferences():

    db = SessionLocal()

    try:

        preferences = (
            db.query(OwnerPreference)
            .order_by(
                OwnerPreference.preference_key
            )
            .all()
        )

        result = {}

        for preference in preferences:

            result[
                preference.preference_key
            ] = preference.preference_value

        return {
            "success": True,
            "preferences": result,
            "count": len(result)
        }

    finally:

        db.close()


# ============================================================
# CLEAR ONE PREFERENCE
# ============================================================

def clear_preference(
    preference_key
):

    db = SessionLocal()

    try:

        if not preference_key:

            return {
                "success": False,
                "message": (
                    "Preference key cannot be empty."
                )
            }

        preference_key = (
            str(preference_key)
            .strip()
            .lower()
        )

        if preference_key not in ALLOWED_PREFERENCES:

            return {
                "success": False,
                "message": (
                    f"Unsupported preference "
                    f"'{preference_key}'."
                )
            }

        begin_write_transaction(db)

        preference = (
            db.query(OwnerPreference)
            .filter(
                OwnerPreference.preference_key
                == preference_key
            )
            .first()
        )

        if not preference:

            return {
                "success": True,
                "message": (
                    f"No saved preference found "
                    f"for '{preference_key}'."
                )
            }

        db.delete(preference)

        db.commit()

        return {
            "success": True,
            "message": (
                f"Preference '{preference_key}' "
                "cleared successfully."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error clearing preference: {str(e)}"
            )
        }

    finally:

        db.close()