from app.database.db import SessionLocal
from app.database.models import Product


db = SessionLocal()


products = [
    Product(
        name="Aashirvaad Atta 5kg",
        sku="ATTA5KG",
        unit="packet",
        cost_price=220,
        selling_price=250,
        mrp=260,
        quantity=20,
        reorder_level=5,
        gst_rate=5,
        hsn_code="1101"
    ),

    Product(
        name="Tata Salt 1kg",
        sku="SALT1KG",
        unit="packet",
        cost_price=20,
        selling_price=25,
        mrp=28,
        quantity=30,
        reorder_level=5,
        gst_rate=5,
        hsn_code="2501"
    ),

    Product(
        name="Maggi 70g",
        sku="MAGGI70",
        unit="packet",
        cost_price=12,
        selling_price=14,
        mrp=14,
        quantity=50,
        reorder_level=10,
        gst_rate=12,
        hsn_code="1902"
    ),

    Product(
        name="Amul Butter 100g",
        sku="BUTTER100",
        unit="piece",
        cost_price=55,
        selling_price=60,
        mrp=62,
        quantity=15,
        reorder_level=5,
        gst_rate=12,
        hsn_code="0405"
    ),

    Product(
        name="Fortune Sunflower Oil 1L",
        sku="OIL1L",
        unit="litre",
        cost_price=110,
        selling_price=125,
        mrp=130,
        quantity=20,
        reorder_level=5,
        gst_rate=5,
        hsn_code="1512"
    )
]


for product in products:
    db.add(product)


db.commit()
db.close()

print("Products added successfully!")