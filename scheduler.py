"""
Scheduler — רץ על Railway 24/7
מפעיל את neworder_shva.py בזמנים הנכונים:
  א-ה: 19:30
  שישי: 14:00
  שבת: לא רץ
"""

import schedule
import time
import subprocess
from datetime import datetime

def should_run_today():
    """האם צריך לרוץ היום? לא בשבת."""
    return datetime.now().weekday() != 5  # 5 = שבת

def run_sync():
    if not should_run_today():
        print("🕍 שבת — אין ריצה")
        return
    print(f"🚀 מפעיל סנכרון — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    subprocess.run(["python", "neworder_shva.py"], check=False)

# ימים א-ה: 19:30
schedule.every().sunday.at("19:30").do(run_sync)
schedule.every().monday.at("19:30").do(run_sync)
schedule.every().tuesday.at("19:30").do(run_sync)
schedule.every().wednesday.at("19:30").do(run_sync)
schedule.every().thursday.at("19:30").do(run_sync)

# שישי: 14:00
schedule.every().friday.at("14:00").do(run_sync)

print("⏱️  Scheduler פעיל — ממתין לזמן הריצה...")
print("   א-ה: 19:30 | שישי: 14:00 | שבת: לא רץ")

while True:
    schedule.run_pending()
    time.sleep(60)
