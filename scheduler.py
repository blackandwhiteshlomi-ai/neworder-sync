"""
Scheduler — רץ על Railway 24/7
"""

import time
import subprocess
import sys
from datetime import datetime, timezone, timedelta

def log(msg):
    """הדפסה עם flush כדי שRailway יראה את הלוגים"""
    print(msg, flush=True)
    sys.stdout.flush()

def israel_now():
    utc_now = datetime.now(timezone.utc)
    month = utc_now.month
    offset = timedelta(hours=3) if 4 <= month <= 10 else timedelta(hours=2)
    return utc_now + offset

def check_and_run():
    now    = israel_now()
    hour   = now.hour
    minute = now.minute
    wd     = now.weekday()
    # 0=שני, 1=שלישי, 2=רביעי, 3=חמישי, 4=שישי, 5=שבת, 6=ראשון

    if wd == 5:
        return  # שבת

    is_sun_thu = wd in [6, 0, 1, 2, 3]
    is_friday  = wd == 4

    if hour == 19 and minute == 50 and is_sun_thu:
        log(f"\n🚀 ריצה יומית — {now.strftime('%d/%m/%Y %H:%M')}")
        subprocess.run(["python", "neworder_shva.py"], check=False)

    elif hour == 14 and minute == 0 and is_friday:
        log(f"\n🚀 ריצה שישי — {now.strftime('%d/%m/%Y %H:%M')}")
        subprocess.run(["python", "neworder_shva.py"], check=False)

# ── הפעלה ──
log("=" * 40)
log("⏱️  Scheduler פעיל!")
log(f"   שעה ישראל: {israel_now().strftime('%d/%m/%Y %H:%M')}")
log("   א-ה: 19:30 | שישי: 14:00 | שבת: לא רץ")
log("=" * 40)

while True:
    check_and_run()
    time.sleep(60)
