from app.tools.reorder import get_reorder_recommendations


print("\n--- REORDER RECOMMENDATIONS ---")

result = get_reorder_recommendations()

print(result)


print("\n--- REORDER DETAILS ---")

if result["success"]:

    if result["products"]:

        for product in result["products"]:

            print(
                f"Product: {product['product']}"
            )

            print(
                f"SKU: {product['sku']}"
            )

            print(
                f"Current Stock: "
                f"{product['current_stock']} "
                f"{product['unit']}"
            )

            print(
                f"Reorder Level: "
                f"{product['reorder_level']}"
            )

            print(
                f"Suggested Reorder Quantity: "
                f"{product['suggested_reorder_quantity']} "
                f"{product['unit']}"
            )

            print(
                f"Cost Price: "
                f"₹{product['cost_price']:.2f}"
            )

            print("-" * 40)

    else:

        print("No products currently need reordering.")

else:

    print(
        f"Error: {result['message']}"
    )