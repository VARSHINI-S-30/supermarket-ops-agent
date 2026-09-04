from app.tools.product_search import search_products


print("\n--- SEARCH FOR MAGGI ---")
result = search_products("Maggi")
print(result)


print("\n--- SEARCH FOR ATTA ---")
result = search_products("Atta")
print(result)


print("\n--- SEARCH FOR NON-EXISTING PRODUCT ---")
result = search_products("Chocolate")
print(result)


print("\n--- EMPTY SEARCH ---")
result = search_products("")
print(result)