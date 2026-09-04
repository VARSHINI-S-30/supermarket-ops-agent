from app.database.db import SessionLocal
from app.database.models import Customer


db = SessionLocal()


customer = Customer(
    name="Ramesh",
    phone="9876543210",
    credit_balance=0
)

db.add(customer)
db.commit()
db.close()

print("Customer added successfully!")