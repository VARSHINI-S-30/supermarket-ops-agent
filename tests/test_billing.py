from app.tools.billing import (
    create_bill,
    add_item_to_bill,
    finalize_bill,
    update_bill_item,
    get_bill
)


print("\n--- CREATE BILL ---")

result = create_bill()

print(result)

bill_id = result["bill_id"]


print("\n--- ADD AASHIRVAAD ATTA ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku="ATTA5KG",
    quantity=2
)

print(result)


print("\n--- ADD MAGGI ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku="MAGGI70",
    quantity=3
)

print(result)


print("\n--- INVALID PRODUCT ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku="UNKNOWN",
    quantity=1
)

print(result)


print("\n--- INVALID QUANTITY ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku="MAGGI70",
    quantity=-2
)

print(result)


print("\n--- EXCESSIVE QUANTITY ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku="MAGGI70",
    quantity=100000
)

print(result)


print("\n--- GET DRAFT BILL ---")

result = get_bill(bill_id)

print(result)


print("\n--- FINALIZE BILL ---")

result = finalize_bill(
    bill_id=bill_id,
    payment_mode="upi"
)

print(result)


print("\n--- GET FINALIZED BILL ---")

result = get_bill(bill_id)

print(result)


print("\n--- FINALIZE AGAIN ---")

result = finalize_bill(
    bill_id=bill_id,
    payment_mode="cash"
)

print(result)


print("\n--- CREATE BILL FOR EDITING ---")

edit_bill = create_bill()

print(edit_bill)

edit_bill_id = edit_bill["bill_id"]


print("\n--- ADD MAGGI ---")

result = add_item_to_bill(
    bill_id=edit_bill_id,
    sku="MAGGI70",
    quantity=3
)

print(result)


print("\n--- GET BILL AFTER ADDING MAGGI ---")

result = get_bill(edit_bill_id)

print(result)


print("\n--- CHANGE MAGGI FROM 3 TO 5 ---")

result = update_bill_item(
    bill_id=edit_bill_id,
    sku="MAGGI70",
    quantity=5
)

print(result)


print("\n--- GET BILL AFTER EDIT ---")

result = get_bill(edit_bill_id)

print(result)


print("\n--- REMOVE MAGGI ---")

result = update_bill_item(
    bill_id=edit_bill_id,
    sku="MAGGI70",
    quantity=0
)

print(result)


print("\n--- GET BILL AFTER REMOVING MAGGI ---")

result = get_bill(edit_bill_id)

print(result)


print("\n--- UPDATE NON-EXISTING ITEM ---")

result = update_bill_item(
    bill_id=edit_bill_id,
    sku="ATTA5KG",
    quantity=2
)

print(result)


print("\n--- GET INVALID BILL ---")

result = get_bill(99999)

print(result)