"""
Scheduler — רץ על Railway 24/7
"""

import time
import subprocess
import sys
from datetime import datetime, timezone, timedelta

def log(msg):
    print(msg, flush=True)

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

    if wd == 5:
        return  # שבת

    is_sun_thu = wd in [6, 0, 1, 2, 3]
    is_friday  = wd == 4

    if hour == 22 and minute == 30 and is_sun_thu:
        log(f"\n🚀 ריצה יומית — {now.strftime('%d/%m/%Y %H:%M')}")
        # הרץ את הסקריפט ישירות בתוך אותו process עם stdout מחובר
        result = subprocess.run(
            ["python", "-u", "neworder_shva.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=False
        )
        log(f"✅ סיום ריצה (exit: {result.returncode})")

    elif hour == 14 and minute == 0 and is_friday:
        log(f"\n🚀 ריצה שישי — {now.strftime('%d/%m/%Y %H:%M')}")
        result = subprocess.run(
            ["python", "-u", "neworder_shva.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=False
        )
        log(f"✅ סיום ריצה (exit: {result.returncode})")

log("=" * 40)
log("⏱️  Scheduler פעיל!")
log(f"   שעה ישראל: {israel_now().strftime('%d/%m/%Y %H:%M')}")
log("   א-ה: 19:50 (בדיקה) | שישי: 14:00 | שבת: לא רץ")
log("=" * 40)

while True:
    check_and_run()
    time.sleep(60)
