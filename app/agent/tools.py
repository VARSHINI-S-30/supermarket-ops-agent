from app.tools.inventory import (
    add_product,
    receive_stock,
    check_stock,
    low_stock,
)

from app.tools.health import (
    get_system_health,
)

from app.tools.analytics import (
    get_sales_summary,
    get_daily_sales,
    get_daily_close,
    get_business_health,
)

from app.tools.customers import (
    add_customer,
    search_customers,
    get_customer,
    get_customer_credit,
    record_credit_payment,
    get_customer_credit_summary,
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

from app.tools.reorder import (
    get_reorder_recommendations,
)

from app.services.invoice import (
    generate_invoice,
)

from app.services.analysis_deck import (
    generate_analysis_deck,
)

from app.tools.preferences import (
    set_preference,
    get_preference,
    get_preferences,
    clear_preference,
)
# ============================================================
# TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------
    "get_system_health": {
    "function": get_system_health,
    "description": (
        "Check the health of the supermarket database "
        "and core entities including products, customers, "
        "bills, preferences, Telegram sessions and stock. "
        "Use this for diagnostics or system health questions."
    ),
    "parameters": {},
},
    "add_customer": {
    "function": add_customer,
    "description": (
        "Create a new supermarket customer. "
        "The customer starts with zero outstanding credit. "
        "Phone numbers must be unique."
    ),
    "parameters": {
        "name": {
            "type": "string",
            "description": "Customer full name.",
            "required": True
        },
        "phone": {
            "type": "string",
            "description": "Customer phone number, if available.",
            "required": False
        }
    },
},
    "search_customers": {
    "function": search_customers,
    "description": (
        "Search supermarket customers by name or phone."
    ),
    "parameters": {
        "query": {
            "type": "string",
            "description": (
                "Customer name or phone search text."
            ),
            "required": True
        }
    },
},
  "get_customer": {
    "function": get_customer,
    "description": (
        "Retrieve a customer's name, phone, and "
        "current credit balance."
    ),
    "parameters": {
        "customer_id": {
            "type": "integer",
            "description": "Customer ID.",
            "required": True
        }
    },
},
  "get_customer_credit_summary": {
    "function": get_customer_credit_summary,
    "description": (
        "Get a customer's outstanding credit status "
        "and current balance."
    ),
    "parameters": {
        "customer_id": {
            "type": "integer",
            "description": "Customer ID.",
            "required": True
        }
    },
},  
        "set_preference": {
        "function": set_preference,
        "description": (
            "Save or update a persistent supermarket owner "
            "preference. Preferences survive conversation resets "
            "and application restarts."
        ),
        "parameters": {
            "preference_key": {
                "type": "string",
                "description": (
                    "Preference key: default_payment, "
                    "preferred_brand, shop_name, or gstin."
                ),
                "required": True
            },
            "preference_value": {
                "type": "string",
                "description": (
                    "Value of the preference."
                ),
                "required": True
            }
        },
    },

    "get_preference": {
        "function": get_preference,
        "description": (
            "Retrieve one persistent owner preference."
        ),
        "parameters": {
            "preference_key": {
                "type": "string",
                "description": (
                    "Preference key."
                ),
                "required": True
            }
        },
    },

    "get_preferences": {
        "function": get_preferences,
        "description": (
            "Retrieve all saved persistent owner preferences."
        ),
        "parameters": {},
    },

    "clear_preference": {
        "function": clear_preference,
        "description": (
            "Clear one saved owner preference."
        ),
        "parameters": {
            "preference_key": {
                "type": "string",
                "description": (
                    "Preference key to clear."
                ),
                "required": True
            }
        },
    },

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
        "Finalize a supermarket bill. "
        "Payment mode can be cash, upi, card, or credit. "
        "If payment_mode is omitted, the saved persistent "
        "default_payment preference is automatically used. "
        "An explicitly provided payment mode always overrides "
        "the saved default. Finalization is idempotent and "
        "does not deduct stock twice."
    ),
    "parameters": {
        "bill_id": {
            "type": "integer",
            "description": "The draft bill ID.",
            "required": True
        },
        "payment_mode": {
            "type": "string",
            "description": (
                "Optional payment mode: cash, upi, card, "
                "or credit. If omitted, use the saved "
                "default_payment preference."
            ),
            "required": False
        }
    },
},

    # --------------------------------------------------------
    # KHATA / CREDIT
    # --------------------------------------------------------

    "get_customer_credit": {
    "function": get_customer_credit,
    "description": (
        "Retrieve the current outstanding credit balance "
        "for a specific customer."
    ),
    "parameters": {
        "customer_id": {
            "type": "integer",
            "description": "Customer ID.",
            "required": True
        }
    },
},

    "record_credit_payment": {
    "function": record_credit_payment,
    "description": (
        "Record a payment against a customer's outstanding "
        "credit. The payment cannot exceed the outstanding "
        "balance and cannot make credit negative."
    ),
    "parameters": {
        "customer_id": {
            "type": "integer",
            "description": "Customer ID.",
            "required": True
        },
        "amount": {
            "type": "number",
            "description": (
                "Payment amount in INR."
            ),
            "required": True
        }
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
        "Get sales performance for a date range. "
        "Returns total sales, subtotal, GST collected, "
        "bill count, average bill, payment breakdown, "
        "and top-selling products."
    ),
    "parameters": {
        "start_date": {
            "type": "string",
            "description": (
                "Start date in YYYY-MM-DD format. "
                "If omitted, today is used."
            ),
            "required": False
        },
        "end_date": {
            "type": "string",
            "description": (
                "End date in YYYY-MM-DD format. "
                "If omitted, start_date is used."
            ),
            "required": False
        }
    },
},

    "get_daily_sales": {
    "function": get_daily_sales,
    "description": (
        "Get finalized sales for a specific day. "
        "Returns total sales, GST, bill count, "
        "payment breakdown and top products."
    ),
    "parameters": {
        "sales_date": {
            "type": "string",
            "description": (
                "Date in YYYY-MM-DD format. "
                "If omitted, today's sales are returned."
            ),
            "required": False
        }
    },
},

    "get_daily_close": {
    "function": get_daily_close,
    "description": (
        "Generate the daily operational close summary. "
        "Includes sales, GST collected, payment breakdown, "
        "top products, low-stock products, out-of-stock "
        "products and inventory health."
    ),
    "parameters": {
        "close_date": {
            "type": "string",
            "description": (
                "Closing date in YYYY-MM-DD format. "
                "If omitted, today's date is used."
            ),
            "required": False
        }
    },
},
    
    "get_business_health": {
    "function": get_business_health,
    "description": (
        "Generate a high-level supermarket business health "
        "report using real sales and inventory data. "
        "Returns sales performance, inventory health, "
        "health score and operational recommendations."
    ),
    "parameters": {
        "start_date": {
            "type": "string",
            "description": (
                "Start date in YYYY-MM-DD format."
            ),
            "required": False
        },
        "end_date": {
            "type": "string",
            "description": (
                "End date in YYYY-MM-DD format."
            ),
            "required": False
        }
    },
},

    # --------------------------------------------------------
    # DOCUMENT GENERATION
    # --------------------------------------------------------

    "generate_invoice": {
    "function": generate_invoice,
    "description": (
        "Generate a PDF invoice for a finalized bill. "
        "The invoice uses the owner's persistent shop name "
        "and GSTIN preferences when available."
    ),
    "parameters": {
        "bill_id": {
            "type": "integer",
            "description": "Finalized bill ID.",
            "required": True
        }
    },
},

    "generate_analysis_deck": {
    "function": generate_analysis_deck,
    "description": (
        "Generate a PowerPoint business-analysis deck "
        "using real supermarket data. The deck includes "
        "sales summary, GST collected, payment breakdown, "
        "top-selling products, inventory health and "
        "operational insights."
    ),
    "parameters": {
        "start_date": {
            "type": "string",
            "description": (
                "Start date in YYYY-MM-DD format. "
                "Defaults to today."
            ),
            "required": False
        },
        "end_date": {
            "type": "string",
            "description": (
                "End date in YYYY-MM-DD format. "
                "Defaults to start_date."
            ),
            "required": False
        }
    },
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