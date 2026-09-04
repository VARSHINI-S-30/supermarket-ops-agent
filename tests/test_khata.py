from app.tools.billing import (
    create_bill,
    add_item_to_bill,
    finalize_bill
)

from app.tools.khata import (
    get_customer_credit,
    record_credit_payment
)


print("\n--- INITIAL CREDIT BALANCE ---")

result = get_customer_credit(1)

print(result)


print("\n--- CREATE CREDIT BILL ---")

bill = create_bill(customer_id=1)

print(bill)

bill_id = bill["bill_id"]


print("\n--- ADD MAGGI ---")

result = add_item_to_bill(
    bill_id=bill_id,
    sku="MAGGI70",
    quantity=2
)

print(result)


print("\n--- FINALIZE AS CREDIT ---")

result = finalize_bill(
    bill_id=bill_id,
    payment_mode="credit"
)

print(result)


print("\n--- CREDIT BALANCE AFTER SALE ---")

result = get_customer_credit(1)

print(result)


print("\n--- RECORD CREDIT PAYMENT ---")

result = record_credit_payment(
    customer_id=1,
    amount=10
)

print(result)


print("\n--- FINAL CREDIT BALANCE ---")

result = get_customer_credit(1)

print(result)