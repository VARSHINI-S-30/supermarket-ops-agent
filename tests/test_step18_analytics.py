from datetime import date

from app.database.db import (
    Base,
    engine,
    SessionLocal
)

from app.database.models import (
    Bill,
    Product,
)

from app.tools.analytics import (
    get_sales_summary,
    get_daily_sales,
    get_daily_close,
    get_business_health,
)

from app.services.analysis_deck import (
    generate_analysis_deck,
)


print("=" * 65)
print("STEP 18 - DAILY OPERATIONS & ANALYTICS TEST")
print("=" * 65)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)

print("\n1. Database ready.")


# =========================================================
# TODAY
# =========================================================

today = str(
    date.today()
)

print(
    f"\n2. Testing date: {today}"
)


# =========================================================
# SALES SUMMARY
# =========================================================

result = get_sales_summary(
    start_date=today,
    end_date=today
)

print(
    "\n3. Sales summary:"
)

print(result)

assert result["success"] is True

assert "total_sales" in result

assert "gst_collected" in result

assert "bill_count" in result

assert "payment_breakdown" in result

assert "top_products" in result


# =========================================================
# DAILY SALES
# =========================================================

result = get_daily_sales(
    sales_date=today
)

print(
    "\n4. Daily sales:"
)

print(result)

assert result["success"] is True

assert "total_sales" in result

assert "bill_count" in result


# =========================================================
# DAILY CLOSE
# =========================================================

result = get_daily_close(
    close_date=today
)

print(
    "\n5. Daily close:"
)

print(result)

assert result["success"] is True

assert "sales" in result

assert "payments" in result

assert "top_products" in result

assert "inventory" in result

assert "close_status" in result


# =========================================================
# BUSINESS HEALTH
# =========================================================

result = get_business_health(
    start_date=today,
    end_date=today
)

print(
    "\n6. Business health:"
)

print(result)

assert result["success"] is True

assert "sales" in result

assert "inventory" in result

assert "health_score" in result

assert "health_status" in result

assert "recommendations" in result


# =========================================================
# ANALYSIS DECK
# =========================================================

result = generate_analysis_deck(
    start_date=today,
    end_date=today
)

print(
    "\n7. Analysis deck:"
)

print(result)

assert result["success"] is True

assert "file_path" in result


# =========================================================
# VERIFY FILE
# =========================================================

from pathlib import Path

deck_path = Path(
    result["file_path"]
)

assert deck_path.exists()

assert deck_path.stat().st_size > 0

print(
    f"\n8. Deck generated successfully:"
)

print(
    deck_path
)

print(
    f"Deck size: "
    f"{deck_path.stat().st_size} bytes"
)


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 65)

print(
    "STEP 18 DAILY OPERATIONS & ANALYTICS "
    "TESTS PASSED SUCCESSFULLY"
)

print("=" * 65)