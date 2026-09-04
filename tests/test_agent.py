from app.agent.agent import (
    run_agent
)


print("\n========================================")
print("STEP 10 - AI AGENT TEST")
print("========================================")


# ==========================================================
# TEST 1 - STOCK QUERY
# ==========================================================

print("\n--- TEST 1: STOCK QUERY ---")

result = run_agent(
    "How many Maggi packets do we have?"
)

print(result["message"])


# ==========================================================
# TEST 2 - PRODUCT SEARCH
# ==========================================================

print("\n--- TEST 2: PRODUCT SEARCH ---")

result = run_agent(
    "Do we have Aashirvaad Atta?"
)

print(result["message"])


# ==========================================================
# TEST 3 - LOW STOCK
# ==========================================================

print("\n--- TEST 3: LOW STOCK QUERY ---")

result = run_agent(
    "Which products are low in stock?"
)

print(result["message"])


# ==========================================================
# TEST 4 - SALES
# ==========================================================

print("\n--- TEST 4: SALES QUERY ---")

result = run_agent(
    "What are today's total sales?"
)

print(result["message"])


# ==========================================================
# TEST 5 - REORDER
# ==========================================================

print("\n--- TEST 5: REORDER QUERY ---")

result = run_agent(
    "Which products should I reorder?"
)

print(result["message"])


print("\n========================================")
print("STEP 10 TEST COMPLETED")
print("========================================")