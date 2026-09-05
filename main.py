from app.database.db import engine, Base
from app.database.models import (
    Product,
    Customer,
    Bill,
    BillItem,
    OwnerPreference
)


Base.metadata.create_all(
    bind=engine
)


print(
    "Database tables created successfully!"
)