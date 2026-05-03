"""Verify the new schema columns exist in Supabase. Run after applying schema.sql."""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

required_signal_cols = [
    "risk_class", "confidence", "adv_20", "atr_pct",
    "rr_t1", "rr_t2", "blended_rr",
    "suggested_shares_20k", "suggested_value_20k", "max_loss_20k",
    "strategy_ar", "warnings_ar",
]
required_stock_cols = ["sharia_status"]

print("Probing new columns...")

# Probe by selecting 0 rows with the column
ok = True
for col in required_stock_cols:
    try:
        c.table("stocks").select(col).limit(1).execute()
        print(f"  stocks.{col:30} ✓")
    except Exception as e:
        print(f"  stocks.{col:30} ✗ MISSING ({str(e)[:80]})")
        ok = False

for col in required_signal_cols:
    try:
        c.table("signals").select(col).limit(1).execute()
        print(f"  signals.{col:30} ✓")
    except Exception as e:
        print(f"  signals.{col:30} ✗ MISSING ({str(e)[:80]})")
        ok = False

print()
print("ALL GOOD" if ok else "MIGRATION NEEDED — paste supabase/schema.sql into Supabase SQL Editor")
