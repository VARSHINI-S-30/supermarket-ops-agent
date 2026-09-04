from app.tools.inventory import (
    add_product,
    receive_stock,
    check_stock,
    low_stock,
)

from app.tools.product_search import (
    search_products,
)

from app.tools.billing import (
    create_bill,
    add_item_to_bill,
    update_bill_item,
    get_bill,
    finalize_bill,
)

from app.tools.khata import (
    get_customer_credit,
    record_credit_payment,
)

from app.tools.reorder import (
    get_reorder_recommendations,
)

from app.tools.sales import (
    get_sales_summary,
    get_daily_sales,
    get_daily_close,
)

from app.services.invoice import (
    generate_invoice,
)

from app.services.analysis_deck import (
    generate_analysis_deck,
)


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    "add_product": {
        "function": add_product,
        "description": (
            "Add a new product to the supermarket inventory."
        ),
        "parameters": {
            "name": {
                "type": "string",
                "description": "Product name.",
                "required": True,
            },
            "sku": {
                "type": "string",
                "description": "Unique product SKU.",
                "required": True,
            },
            "unit": {
                "type": "string",
                "description": (
                    "Unit of measurement such as kg, packet, "
                    "piece, litre, or bottle."
                ),
                "required": True,
            },
            "cost_price": {
                "type": "number",
                "description": "Purchase/cost price per unit.",
                "required": True,
            },
            "selling_price": {
                "type": "number",
                "description": "Selling price per unit.",
                "required": True,
            },
            "mrp": {
                "type": "number",
                "description": "Maximum retail price.",
                "required": True,
            },
            "quantity": {
                "type": "number",
                "description": "Initial stock quantity.",
                "required": True,
            },
            "reorder_level": {
                "type": "number",
                "description": "Stock level at which reordering is recommended.",
                "required": True,
            },
            "gst_rate": {
                "type": "number",
                "description": "GST percentage.",
                "required": True,
            },
            "hsn_code": {
                "type": "string",
                "description": "HSN code of the product.",
                "required": True,
            },
        },
    },

    "receive_stock": {
        "function": receive_stock,
        "description": (
            "Receive incoming stock and increase the inventory quantity "
            "for an existing product."
        ),
        "parameters": {
            "sku": {
                "type": "string",
                "description": "SKU of the product.",
                "required": True,
            },
            "quantity": {
                "type": "number",
                "description": "Quantity received.",
                "required": True,
            },
            "cost_price": {
                "type": "number",
                "description": "Optional updated cost price.",
                "required": False,
            },
            "mrp": {
                "type": "number",
                "description": "Optional updated MRP.",
                "required": False,
            },
        },
    },

    "check_stock": {
        "function": check_stock,
        "description": (
            "Check the current inventory stock for a product SKU."
        ),
        "parameters": {
            "sku": {
                "type": "string",
                "description": "Product SKU.",
                "required": True,
            },
        },
    },

    "low_stock": {
        "function": low_stock,
        "description": (
            "Find products whose current stock is at or below "
            "their reorder level."
        ),
        "parameters": {},
    },

    # --------------------------------------------------------
    # PRODUCT SEARCH
    # --------------------------------------------------------

    "search_products": {
        "function": search_products,
        "description": (
            "Search supermarket products by name and return "
            "matching products, SKUs, prices, stock, GST and HSN information."
        ),
        "parameters": {
            "query": {
                "type": "string",
                "description": "Product name or search text.",
                "required": True,
            },
        },
    },

    # --------------------------------------------------------
    # BILLING
    # --------------------------------------------------------

    "create_bill": {
        "function": create_bill,
        "description": (
            "Create a new draft customer bill. Customer ID is optional "
            "unless the bill will eventually use credit/khata."
        ),
        "parameters": {
            "customer_id": {
                "type": "integer",
                "description": "Optional customer ID.",
                "required": False,
            },
        },
    },

    "add_item_to_bill": {
        "function": add_item_to_bill,
        "description": (
            "Add a product and quantity to a draft bill. "
            "The operation validates available stock."
        ),
        "parameters": {
            "bill_id": {
                "type": "integer",
                "description": "Draft bill ID.",
                "required": True,
            },
            "sku": {
                "type": "string",
                "description": "Product SKU.",
                "required": True,
            },
            "quantity": {
                "type": "number",
                "description": "Quantity to add.",
                "required": True,
            },
        },
    },

    "update_bill_item": {
        "function": update_bill_item,
        "description": (
            "Change the quantity of an existing item in a draft bill. "
            "Use quantity zero to remove the item."
        ),
        "parameters": {
            "bill_id": {
                "type": "integer",
                "description": "Draft bill ID.",
                "required": True,
            },
            "sku": {
                "type": "string",
                "description": "Product SKU.",
                "required": True,
            },
            "quantity": {
                "type": "number",
                "description": "New quantity. Use zero to remove the item.",
                "required": True,
            },
        },
    },

    "get_bill": {
        "function": get_bill,
        "description": (
            "Retrieve the current details, items, GST and total "
            "of a bill."
        ),
        "parameters": {
            "bill_id": {
                "type": "integer",
                "description": "Bill ID.",
                "required": True,
            },
        },
    },

    "finalize_bill": {
        "function": finalize_bill,
        "description": (
            "Finalize a draft bill and record the payment mode. "
            "Supported modes are cash, UPI, card and credit."
        ),
        "parameters": {
            "bill_id": {
                "type": "integer",
                "description": "Draft bill ID.",
                "required": True,
            },
            "payment_mode": {
                "type": "string",
                "description": (
                    "Payment mode: cash, upi, card, or credit."
                ),
                "required": False,
            },
        },
    },

    # --------------------------------------------------------
    # KHATA / CREDIT
    # --------------------------------------------------------

    "get_customer_credit": {
        "function": get_customer_credit,
        "description": (
            "Check the outstanding khata/credit balance of a customer."
        ),
        "parameters": {
            "customer_id": {
                "type": "integer",
                "description": "Customer ID.",
                "required": True,
            },
        },
    },

    "record_credit_payment": {
        "function": record_credit_payment,
        "description": (
            "Record a payment made by a customer toward their "
            "outstanding credit balance."
        ),
        "parameters": {
            "customer_id": {
                "type": "integer",
                "description": "Customer ID.",
                "required": True,
            },
            "amount": {
                "type": "number",
                "description": "Payment amount in INR.",
                "required": True,
            },
        },
    },

    # --------------------------------------------------------
    # REORDER
    # --------------------------------------------------------

    "get_reorder_recommendations": {
        "function": get_reorder_recommendations,
        "description": (
            "Generate reorder recommendations for products whose "
            "stock is at or below their reorder level."
        ),
        "parameters": {},
    },

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    "get_sales_summary": {
        "function": get_sales_summary,
        "description": (
            "Get sales summary including bills, subtotal, GST, "
            "total sales, average bill and payment breakdown."
        ),
        "parameters": {
            "date": {
                "type": "string",
                "description": (
                    "Optional date in YYYY-MM-DD format. "
                    "If omitted, use today's date."
                ),
                "required": False,
            },
        },
    },

    "get_daily_sales": {
        "function": get_daily_sales,
        "description": (
            "Get the detailed finalized sales for the current "
            "business day."
        ),
        "parameters": {},
    },

    "get_daily_close": {
        "function": get_daily_close,
        "description": (
            "Get the daily closing summary including received amount, "
            "credit sales and finalized bill information."
        ),
        "parameters": {
            "date": {
                "type": "string",
                "description": (
                    "Optional date in YYYY-MM-DD format. "
                    "If omitted, use today's date."
                ),
                "required": False,
            },
        },
    },

    # --------------------------------------------------------
    # DOCUMENT GENERATION
    # --------------------------------------------------------

    "generate_invoice": {
        "function": generate_invoice,
        "description": (
            "Generate a PDF invoice for a finalized bill."
        ),
        "parameters": {
            "bill_id": {
                "type": "integer",
                "description": "Finalized bill ID.",
                "required": True,
            },
        },
    },

    "generate_analysis_deck": {
        "function": generate_analysis_deck,
        "description": (
            "Generate a PowerPoint business analysis deck "
            "using supermarket sales and inventory data."
        ),
        "parameters": {},
    },
}


# ============================================================
# EXECUTE TOOL
# ============================================================

def execute_tool(tool_name, arguments):
    """
    Execute a registered supermarket tool.

    Parameters
    ----------
    tool_name : str
        Name of the registered tool.

    arguments : dict
        Arguments passed by the AI agent.

    Returns
    -------
    dict
        Tool result.
    """

    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "message": f"Unknown tool: {tool_name}"
        }

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "message": "Tool arguments must be provided as an object."
        }

    tool_info = TOOL_REGISTRY[tool_name]
    function = tool_info["function"]

    try:
        result = function(**arguments)

        return result

    except TypeError as e:
        return {
            "success": False,
            "message": (
                f"Invalid arguments for tool '{tool_name}': {str(e)}"
            )
        }

    except Exception as e:
        return {
            "success": False,
            "message": (
                f"Error executing tool '{tool_name}': {str(e)}"
            )
        }


# ============================================================
# TOOL LIST HELPER
# ============================================================

def get_registered_tools():
    """
    Return the names of all registered tools.
    """

    return list(TOOL_REGISTRY.keys())


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEBULA SUPERMARKET TOOL REGISTRY")
    print("=" * 60)

    print(f"\nTotal tools registered: {len(TOOL_REGISTRY)}")

    for index, tool_name in enumerate(TOOL_REGISTRY, start=1):
        print(f"{index}. {tool_name}")

    print("\nTesting check_stock...")

    result = execute_tool(
        "check_stock",
        {
            "sku": "MAGGI70"
        }
    )

    print(result)

    print("\nTool registry test completed.")