from app.tools.inventory import (
    add_product,
    receive_stock,
    check_stock,
    low_stock
)


print("\n--- ADD PRODUCT ---")

result = add_product(
    name="Parle-G",
    sku="PARLEG",
    unit="packet",
    cost_price=5,
    selling_price=6,
    mrp=6,
    quantity=20,
    reorder_level=5,
    gst_rate=5,
    hsn_code="1905"
)

print(result)


print("\n--- RECEIVE STOCK ---")

result = receive_stock(
    sku="PARLEG",
    quantity=30
)

print(result)



print("\n--- CHECK STOCK ---")

result = check_stock("PARLEG")

print(result)


print("\n--- LOW STOCK ---")

result = low_stock()

print(result)
print(check_stock("UNKNOWN"))
print(receive_stock("PARLEG", -10))