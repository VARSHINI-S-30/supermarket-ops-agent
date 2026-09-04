from datetime import datetime
from zoneinfo import ZoneInfo

from app.tools.sales import (
    get_daily_sales,
    get_sales_summary,
    get_daily_close
)


STORE_TIMEZONE = ZoneInfo("Asia/Kolkata")


print("\n========================================")
print("STEP 6 - SALES SUMMARY TEST")
print("========================================")


# ============================================================
# TEST 1 - TODAY'S SALES
# ============================================================

print("\n--- TEST 1: TODAY'S SALES ---")

result = get_daily_sales()

print(result)


# ============================================================
# TEST 2 - TODAY USING EXPLICIT DATE
# ============================================================

print("\n--- TEST 2: EXPLICIT TODAY DATE ---")

today = datetime.now(
    STORE_TIMEZONE
).strftime("%Y-%m-%d")

result = get_sales_summary(today)

print(result)


# ============================================================
# TEST 3 - DAILY CLOSE
# ============================================================

print("\n--- TEST 3: DAILY CLOSE ---")

result = get_daily_close()

print(result)


# ============================================================
# TEST 4 - DATE WITH NO EXPECTED SALES
# ============================================================

print("\n--- TEST 4: OLD DATE / NO SALES ---")

result = get_sales_summary(
    "2000-01-01"
)

print(result)


# ============================================================
# TEST 5 - INVALID DATE FORMAT
# ============================================================

print("\n--- TEST 5: INVALID DATE FORMAT ---")

result = get_sales_summary(
    "04-09-2026"
)

print(result)


# ============================================================
# TEST 6 - INVALID DATE
# ============================================================

print("\n--- TEST 6: INVALID CALENDAR DATE ---")

result = get_sales_summary(
    "2026-02-30"
)

print(result)


# ============================================================
# TEST 7 - EMPTY DATE
# ============================================================

print("\n--- TEST 7: EMPTY DATE ---")

result = get_sales_summary("")

print(result)


# ============================================================
# TEST 8 - INVALID DATA TYPE
# ============================================================

print("\n--- TEST 8: INVALID DATE TYPE ---")

result = get_sales_summary(12345)

print(result)


print("\n========================================")
print("STEP 6 TEST COMPLETED")
print("========================================")