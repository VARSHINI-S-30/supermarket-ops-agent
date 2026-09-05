from decimal import Decimal, InvalidOperation


ALLOWED_PAYMENT_MODES = {
    "cash",
    "upi",
    "card",
    "credit"
}


def validate_positive_quantity(quantity):
    """
    Validate that quantity is a positive number.
    """

    try:
        value = Decimal(str(quantity))
    except (InvalidOperation, ValueError, TypeError):

        return {
            "success": False,
            "message": "Quantity must be a valid number."
        }

    if value <= 0:

        return {
            "success": False,
            "message": "Quantity must be greater than zero."
        }

    return {
        "success": True,
        "value": value
    }


def validate_payment_mode(payment_mode):
    """
    Validate supported payment modes.
    """

    if payment_mode is None:

        return {
            "success": False,
            "message": "Payment mode is required."
        }

    payment_mode = str(
        payment_mode
    ).strip().lower()

    if payment_mode not in ALLOWED_PAYMENT_MODES:

        return {
            "success": False,
            "message": (
                "Invalid payment mode. "
                "Allowed values: cash, upi, card, credit."
            )
        }

    return {
        "success": True,
        "value": payment_mode
    }


def validate_gst_rate(gst_rate):
    """
    Validate GST percentage.
    """

    try:
        value = Decimal(str(gst_rate))
    except (InvalidOperation, ValueError, TypeError):

        return {
            "success": False,
            "message": "GST rate must be a valid number."
        }

    if value < 0 or value > 100:

        return {
            "success": False,
            "message": "GST rate must be between 0 and 100."
        }

    return {
        "success": True,
        "value": value
    }


def validate_price(
    cost_price,
    selling_price,
    mrp
):
    """
    Validate supermarket pricing rules.

    Rules:
    selling price >= cost price
    selling price <= MRP
    """

    try:

        cost = Decimal(
            str(cost_price)
        )

        selling = Decimal(
            str(selling_price)
        )

        maximum_retail = Decimal(
            str(mrp)
        )

    except (InvalidOperation, ValueError, TypeError):

        return {
            "success": False,
            "message": "Prices must be valid numbers."
        }

    if cost < 0:

        return {
            "success": False,
            "message": "Cost price cannot be negative."
        }

    if selling < 0:

        return {
            "success": False,
            "message": "Selling price cannot be negative."
        }

    if maximum_retail < 0:

        return {
            "success": False,
            "message": "MRP cannot be negative."
        }

    if selling < cost:

        return {
            "success": False,
            "message": (
                "Selling price cannot be below cost price."
            )
        }

    if selling > maximum_retail:

        return {
            "success": False,
            "message": (
                "Selling price cannot be above MRP."
            )
        }

    return {
        "success": True,
        "cost_price": cost,
        "selling_price": selling,
        "mrp": maximum_retail
    }


def validate_stock_quantity(quantity):
    """
    Ensure stock never becomes negative.
    """

    try:
        value = Decimal(str(quantity))
    except (InvalidOperation, ValueError, TypeError):

        return {
            "success": False,
            "message": "Stock quantity must be numeric."
        }

    if value < 0:

        return {
            "success": False,
            "message": (
                "Stock quantity cannot be negative."
            )
        }

    return {
        "success": True,
        "value": value
    }