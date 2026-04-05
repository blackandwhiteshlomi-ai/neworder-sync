"""
Scheduler — רץ על Railway 24/7
משתמש ב-zoneinfo (מובנה ב-Python 3.9+, ללא התקנה)
מתאים אוטומטית לשעון קיץ/חורף ישראל
"""

import time
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")

def israel_now():
    return datetime.now(ISRAEL_TZ)

def check_and_run():
    now    = israel_now()
    hour   = now.hour
    minute = now.minute
    wd     = now.weekday()
    # Python weekday: 0=שני, 1=שלישי, 2=רביעי, 3=חמישי, 4=שישי, 5=שבת, 6=ראשון

    if wd == 5:
        return  # שבת — לא רצים

    is_sun_thu = wd in [6, 0, 1, 2, 3]
    is_friday  = wd == 4

    if hour == 19 and minute == 30 and is_sun_thu:
        print(f"\n🚀 ריצה יומית — {now.strftime('%d/%m/%Y %H:%M %Z')}")
        subprocess.run(["python", "neworder_shva.py"], check=False)

    elif hour == 14 and minute == 0 and is_friday:
        print(f"\n🚀 ריצה שישי — {now.strftime('%d/%m/%Y %H:%M %Z')}")
        subprocess.run(["python", "neworder_shva.py"], check=False)

print("⏱️  Scheduler פעיל!")
print(f"   שעה: {israel_now().strftime('%d/%m/%Y %H:%M %Z')}")
print("   א-ה: 19:30 | שישי: 14:00 | שבת: לא רץ")
print("   שעון קיץ/חורף: אוטומטי (Asia/Jerusalem)")

while True:
    check_and_run()
    time.sleep(60)
