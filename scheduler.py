"""
Scheduler — רץ על Railway 24/7
מחשב שעון ישראל ידנית:
  קיץ (מרץ-אוקטובר): UTC+3
  חורף (נובמבר-פברואר): UTC+2
"""

import time
import subprocess
from datetime import datetime, timezone, timedelta

def israel_now():
    """מחזיר שעת ישראל — UTC+3 קיץ, UTC+2 חורף"""
    utc_now = datetime.now(timezone.utc)
    month = utc_now.month
    # שעון קיץ: אפריל-אוקטובר = UTC+3
    # שעון חורף: נובמבר-מרץ = UTC+2
    if 4 <= month <= 10:
        offset = timedelta(hours=3)
    else:
        offset = timedelta(hours=2)
    return utc_now + offset

def check_and_run():
    now    = israel_now()
    hour   = now.hour
    minute = now.minute
    wd     = now.weekday()
    # Python: 0=שני, 1=שלישי, 2=רביעי, 3=חמישי, 4=שישי, 5=שבת, 6=ראשון

    if wd == 5:
        return  # שבת

    is_sun_thu = wd in [6, 0, 1, 2, 3]
    is_friday  = wd == 4

    if hour == 19 and minute == 30 and is_sun_thu:
        print(f"\n🚀 ריצה יומית — {now.strftime('%d/%m/%Y %H:%M')}")
        subprocess.run(["python", "neworder_shva.py"], check=False)

    elif hour == 14 and minute == 0 and is_friday:
        print(f"\n🚀 ריצה שישי — {now.strftime('%d/%m/%Y %H:%M')}")
        subprocess.run(["python", "neworder_shva.py"], check=False)

print("⏱️  Scheduler פעיל!")
print(f"   שעה ישראל: {israel_now().strftime('%d/%m/%Y %H:%M')}")
print("   א-ה: 19:30 | שישי: 14:00 | שבת: לא רץ")

while True:
    check_and_run()
    time.sleep(60)
