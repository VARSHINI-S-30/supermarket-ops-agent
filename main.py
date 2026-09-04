from app.database.db import engine, Base
from app.database.models import Product, Customer


Base.metadata.create_all(bind=engine)

print("Database created successfully!")