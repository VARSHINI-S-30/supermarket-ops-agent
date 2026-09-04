from app.agent.tools import (
    TOOLS,
    execute_tool,
    get_tool_names,
    get_tool_description,
    get_all_tool_descriptions
)


print("\n========================================")
print("STEP 9 - AGENT TOOL LAYER TEST")
print("========================================")


# ==========================================================
# TEST 1 - TOOL REGISTRY
# ==========================================================

print("\n--- TEST 1: TOOL REGISTRY ---")

tool_names = get_tool_names()

print(f"Total tools registered: {len(tool_names)}")

for name in tool_names:
    print(f"  - {name}")


# ==========================================================
# TEST 2 - TOOL DESCRIPTION
# ==========================================================

print("\n--- TEST 2: TOOL DESCRIPTION ---")

description = get_tool_description(
    "check_stock"
)

print(description)


# ==========================================================
# TEST 3 - ALL TOOL DESCRIPTIONS
# ==========================================================

print("\n--- TEST 3: ALL TOOL DESCRIPTIONS ---")

all_descriptions = get_all_tool_descriptions()

print(
    f"Descriptions available: "
    f"{len(all_descriptions)}"
)


# ==========================================================
# TEST 4 - CHECK STOCK TOOL
# ==========================================================

print("\n--- TEST 4: EXECUTE CHECK STOCK ---")

result = execute_tool(
    "check_stock",
    {
        "sku": "MAGGI70"
    }
)

print(result)


# ==========================================================
# TEST 5 - SEARCH PRODUCT TOOL
# ==========================================================

print("\n--- TEST 5: EXECUTE PRODUCT SEARCH ---")

result = execute_tool(
    "search_products",
    {
        "query": "Maggi"
    }
)

print(result)


# ==========================================================
# TEST 6 - INVALID TOOL
# ==========================================================

print("\n--- TEST 6: INVALID TOOL ---")

result = execute_tool(
    "does_not_exist",
    {}
)

print(result)


# ==========================================================
# TEST 7 - INVALID ARGUMENTS
# ==========================================================

print("\n--- TEST 7: INVALID ARGUMENTS ---")

result = execute_tool(
    "check_stock",
    {}
)

print(result)


print("\n========================================")
print("STEP 9 TEST COMPLETED")
print("========================================")