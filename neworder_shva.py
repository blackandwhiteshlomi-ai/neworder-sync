"""
NewOrder — שידורים לשב"א → Base44
מסופים: 2722802011=יציל, 2722732015=גמא
"""

import os, json, requests
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

load_dotenv()

URL_BASE  = "https://cellular.neworder.co.il/heb"
URL_LOGIN = f"{URL_BASE}/login.aspx"
URL_SHVA  = f"{URL_BASE}/reports/reportgenerator.aspx"

USERNAME  = os.getenv("NEWORDER_USERNAME", "רבקה")
COMPANY   = os.getenv("NEWORDER_COMPANY",  "שחור לבן")
PASSWORD  = os.getenv("NEWORDER_PASSWORD", "")

B44_APP   = os.getenv("BASE44_APP_ID", "68fd2f221049dfcfb0277c40")
B44_KEY   = os.getenv("BASE44_API_KEY", "f8f98495094f4d55a3fb4fdfdf108260")
B44_URL   = f"https://base44.app/api/apps/{B44_APP}"
B44_HDR   = {"Content-Type": "application/json", "api_key": B44_KEY}

TERMINALS = {
    "2722802011": "גמא",
    "2722732015": "יציל",
}

# מנהלים לקבל התראות
MANAGER_PHONES = ["972542272345"]  # זיו


# ─── שליחת התראה WhatsApp ──────────────────────────────────
def send_whatsapp_alert(date_str: str, missing_terminals: list):
    """שולח התראה למנהלים כשמסוף לא סגר קופה עד 21:00"""
    if not missing_terminals:
        return

    names = [TERMINALS.get(t, t) for t in missing_terminals]
    msg = (
        f"⚠️ *התראה — קופה לא נסגרה!*\n\n"
        f"📅 תאריך: {date_str}\n"
        f"🖥️ מסופים: {', '.join(names)}\n\n"
        f"נא לסגור קופה ולשדר לשב\"א בהקדם."
    )

    print(f"\n📱 שולח התראה WhatsApp: {names}")

    # שמור לקובץ לוג
    with open("alerts.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} — {msg}\n\n")

    # שלח ל-Base44 MessageQueue
    for phone in MANAGER_PHONES:
        try:
            r = requests.post(
                f"{B44_URL}/entities/MessageQueue",
                headers=B44_HDR,
                json={
                    "message_type": "whatsapp",
                    "recipient": phone,
                    "content": msg,
                    "priority": "high",
                    "status": "pending",
                    "related_entity_type": "NOSBroadcast",
                },
                timeout=10
            )
            if r.ok:
                print(f"  ✅ התראה נשלחה ל-{phone}")
            else:
                print(f"  ❌ שגיאה: {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ שגיאת שליחה: {e}")


# ─── כניסה ────────────────────────────────────────────────
def login(page):
    print("🔐 מתחבר...")
    page.goto(URL_LOGIN, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)

    # מלא לפי סדר קבוע: שם משתמש, שם חברה, סיסמה
    # שלב 1 — מצא את כל שדות הטקסט לפי סדר
    text_inputs = page.query_selector_all("input[type='text']")
    pass_inputs = page.query_selector_all("input[type='password']")
    
    print(f"  נמצאו {len(text_inputs)} שדות טקסט, {len(pass_inputs)} שדות סיסמה")
    
    # מלא שדות טקסט: ראשון=משתמש, שני=חברה
    if len(text_inputs) >= 1:
        text_inputs[0].fill(USERNAME)
        print("  ✓ משתמש")
    if len(text_inputs) >= 2:
        text_inputs[1].fill(COMPANY)
        print("  ✓ חברה")
    
    # מלא סיסמה
    if len(pass_inputs) >= 1:
        pass_inputs[0].fill(PASSWORD)
        print("  ✓ סיסמה")

    cb = page.query_selector("input[type='checkbox']")
    if cb and not cb.is_checked():
        cb.click(); page.wait_for_timeout(300)
    print("  ✓ Checkbox")

    btn = page.query_selector("input[type='submit'], button[type='submit'], button")
    if btn: btn.click()
    page.wait_for_timeout(3000)

    if "login" in page.url.lower():
        raise Exception("❌ כניסה נכשלה")
    print("✅ מחובר!")


# ─── הכנסת תאריך ישירה ────────────────────────────────────
def fill_date(page, field_index: int, date_str: str):
    date_inputs = page.query_selector_all("input[type='text']")
    if field_index >= len(date_inputs):
        print(f"  ⚠️ לא נמצא שדה {field_index}")
        return

    inp = date_inputs[field_index]
    inp.click()
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    inp.click()
    page.wait_for_timeout(200)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.wait_for_timeout(100)
    page.keyboard.type(date_str, delay=80)
    page.wait_for_timeout(300)

    # לחץ על השדה השני לסגירה
    other = 1 - field_index
    date_inputs2 = page.query_selector_all("input[type='text']")
    if other < len(date_inputs2):
        date_inputs2[other].click()
        page.wait_for_timeout(400)

    print(f"  ✓ תאריך {date_str} (שדה {field_index})")


# ─── שליפת כל השידורים לתאריך ────────────────────────────
def get_all_shva(page, date_str: str) -> list:
    print(f"\n📊 שולף שידורים — {date_str}")

    # ── נווט לשידורים לשב"א ──
    page.goto(URL_SHVA, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)

    try:
        page.get_by_text("הנהלת חשבונות", exact=True).click()
        page.wait_for_timeout(600)
        page.get_by_text('שידורים לשב"א', exact=True).click()
        page.wait_for_timeout(1500)
        print('  ✓ ניווט לשידורים לשב"א')
    except Exception as e:
        print(f"  ⚠️ שגיאת ניווט: {e}")

    # ── מלא תאריכים ──
    fill_date(page, 0, date_str)  # מתאריך
    page.wait_for_timeout(500)
    fill_date(page, 1, date_str)  # עד תאריך
    page.wait_for_timeout(500)

    # ── וודא שהתאריכים נכנסו ──
    try:
        date_inputs = page.query_selector_all("input[type='text']")
        val0 = date_inputs[0].input_value() if len(date_inputs) > 0 else "?"
        val1 = date_inputs[1].input_value() if len(date_inputs) > 1 else "?"
        print(f"  📅 שדה 0: {val0} | שדה 1: {val1}")
    except Exception as e:
        print(f"  ⚠️ לא הצלחתי לקרוא שדות: {e}")

    # ── לחץ הצג דו"ח — JavaScript ישיר ──
    try:
        # סגור כל popup/לוח פתוח
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
        
        # לחץ על גוף הדף לסגירה
        page.mouse.click(10, 10)
        page.wait_for_timeout(500)

        # לחץ על הכפתור ישירות דרך JavaScript
        result = page.evaluate("""
            () => {
                var btns = document.querySelectorAll('button');
                var allBtns = [];
                for(var btn of btns) {
                    var t = (btn.innerText || '').trim();
                    allBtns.push(t);
                    if(t.includes('הצג')) {
                        btn.click();
                        return 'clicked: ' + t;
                    }
                }
                var inputs = document.querySelectorAll('input[type=button], input[type=submit]');
                for(var inp of inputs) {
                    var v = (inp.value || '').trim();
                    allBtns.push(v);
                    if(v.includes('הצג')) {
                        inp.click();
                        return 'clicked input: ' + v;
                    }
                }
                return 'not found. buttons: ' + allBtns.join(', ');
            }
        """)
        print(f"  ✓ JavaScript: {result}")
        page.wait_for_timeout(5000)
        
    except Exception as e:
        print(f"  ⚠️ שגיאת כפתור: {e}")

    # ── צילום מסך ──
    safe = date_str.replace("/", "-")
    page.screenshot(path=f"shva_{safe}.png")
    print(f"  📸 shva_{safe}.png")

    # ── חלץ טבלה ──
    rows = []
    try:
        page.wait_for_selector("table", timeout=8000)

        ths = page.query_selector_all("table th")
        if not ths:
            ths = page.query_selector_all("table tr:first-child td")
        headers = [h.inner_text().strip() for h in ths]
        print(f"  עמודות: {headers}")

        for tr in page.query_selector_all("table tr")[1:]:
            tds = [td.inner_text().strip() for td in tr.query_selector_all("td")]
            if not tds: continue
            row = dict(zip(headers, tds)) if (headers and len(tds) == len(headers)) \
                  else {f"col{i}": v for i, v in enumerate(tds)}
            rows.append(row)
            print(f"    {row}")

    except PWTimeout:
        body = page.inner_text("body")
        if "אין תוצאות" in body:
            print("  → אין שידורים לתאריך זה")
        else:
            print("  ⚠️ לא נמצאה טבלה")

    return rows


# ─── עיבוד שורות → סיכום לפי מסוף ───────────────────────
def process_rows(rows: list, date_str: str) -> dict:
    """
    מקבל את שורות הטבלה, מחזיר dict עם סיכום לפי מסוף.
    {terminal_id: {name, total, transactions, date}}
    """
    result = {}

    for row in rows:
        # ── מצא מסוף ──
        # מחפש בכל ערכי השורה את מספר המסוף
        terminal_id = None
        for cell_val in row.values():
            cell_str = str(cell_val).strip()
            for tid in TERMINALS:
                if tid == cell_str or tid in cell_str:
                    terminal_id = tid
                    break
            if terminal_id:
                break

        if not terminal_id:
            continue

        # ── מצא סכום ──
        # לפי הנתונים שנראו:
        # col0=תאריך, col1=תאריך שידור, col2=מסוף, col3=אסמכתא
        # col4=מספר שידור, col5=עסקאות חובה, col6=סה"כ חובה
        # col7=עסקאות זיכוי, col8=סה"כ זיכויים, col9=סניף
        # col10=מספר Z, col11=סה"כ כולל
        total = 0.0
        
        # נסה לפי שם עמודה עם כותרת
        for key in row:
            if any(k in str(key) for k in ['חובה', 'סכום', 'כולל']):
                try:
                    v = str(row[key]).replace(",","").replace("₪","").strip()
                    fv = float(v)
                    if fv > 0:
                        total = fv
                        break
                except:
                    pass

        # אם לא נמצא לפי שם — לפי מיקום (col6 = סה"כ חובה)
        if total == 0.0:
            for col in ['col6', 'col11', 'col5']:
                try:
                    v = str(row.get(col, "")).replace(",","").replace("₪","").strip()
                    fv = float(v)
                    if fv > 0:
                        total = fv
                        break
                except:
                    pass

        # ── מצא מספר עסקאות ──
        txn_count = 0
        # col5 = מספר עסקאות חובה
        for col in ['col5', 'col4']:
            try:
                txn_count = int(str(row.get(col, "0")).strip())
                if txn_count > 0:
                    break
            except:
                pass
        # נסה לפי שם עמודה
        for key in row:
            if 'עסקאות' in str(key):
                try:
                    v = int(str(row[key]).strip())
                    if v > 0:
                        txn_count = v
                        break
                except:
                    pass

        # ── מצא תאריך ושעת שידור מקורי ──
        # col1 = תאריך שידור בפורמט DD/MM/YYYY HH:MM
        broadcast_at = None
        for col in ['col1', 'col0']:
            val = str(row.get(col, "")).strip()
            if "/" in val and ":" in val:
                try:
                    # פורמט: DD/MM/YYYY HH:MM
                    dt = datetime.strptime(val, "%d/%m/%Y %H:%M")
                    broadcast_at = dt.isoformat()
                    break
                except:
                    pass

        name = TERMINALS[terminal_id]
        if terminal_id not in result:
            result[terminal_id] = {
                "name": name,
                "total": 0.0,
                "transactions": 0,
                "date": date_str,
                "broadcast_at": broadcast_at,
                "raw": []
            }
        result[terminal_id]["total"] += total
        result[terminal_id]["transactions"] += txn_count
        if broadcast_at:
            result[terminal_id]["broadcast_at"] = broadcast_at
        result[terminal_id]["raw"].append(row)

    return result


# ─── שמירה ל-Base44 → NOSBroadcast ──────────────────────
def save_to_base44(date_str: str, terminal_id: str, data: dict):
    d, m, y = date_str.split("/")
    record = {
        "date":               f"{y}-{m}-{d}",
        "terminal_id":        terminal_id,
        "terminal_name":      data["name"],
        "total_amount":       data["total"],
        "transactions_count": data["transactions"],
        "status":             "ok" if data["total"] > 0 else "missing",
        "synced_at":          datetime.now().isoformat(),
        "broadcast_at":       data.get("broadcast_at"),
    }
    r = requests.post(
        f"{B44_URL}/entities/NOSBroadcast",
        headers=B44_HDR,
        json=record,
        timeout=15
    )
    if r.ok:
        print(f"  ✅ NOSBroadcast: {data['name']} = ₪{data['total']:,.2f}")
    else:
        print(f"  ❌ Base44 שגיאה: {r.text[:300]}")


# ─── ריצה ─────────────────────────────────────────────────
def run(test_date: str = None):
    today   = test_date or datetime.now().strftime("%d/%m/%Y")
    weekday = datetime.strptime(today, "%d/%m/%Y").weekday()

    if weekday == 5 and not test_date:
        print("🕍 שבת — אין ריצה"); return

    print(f"\n{'='*55}")
    print(f"🚀 שידורים לשב\"א — {today}")
    print(f"{'='*55}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        ctx  = browser.new_context(viewport={"width": 1280, "height": 800}, locale="he-IL")
        page = ctx.new_page()

        try:
            login(page)

            # שלוף את כל השידורים
            rows = get_all_shva(page, today)

            # עבד לפי מסוף
            summary = process_rows(rows, today)

            # ── סיכום ──
            print(f"\n{'='*55}")
            print(f"📋 סיכום — {today}")
            print(f"{'='*55}")

            missing = []
            for tid, data in summary.items():
                if data["total"] > 0:
                    print(f"  ✅ {data['name']:8s}: ₪{data['total']:>12,.2f}  ({data['transactions']} עסקאות)")
                else:
                    print(f"  ❌ {data['name']:8s}: לא נסגר!")
                    missing.append(data["name"])

            # בדוק מסופים שחסרים לגמרי מהתוצאות
            for tid, name in TERMINALS.items():
                if tid not in summary:
                    print(f"  ❌ {name:8s}: אין שידור!")
                    missing.append(name)

            if missing:
                print(f"\n⚠️  לא נסגרו: {', '.join(missing)}")
            else:
                print(f"\n✅ כל המסופים נסגרו!")

            # שמור ל-Base44
            if B44_KEY:
                for tid, data in summary.items():
                    save_to_base44(today, tid, data)
            else:
                print("\n💡 הוסף BASE44_API_KEY ל-.env כדי לשמור ב-Base44")

            # שמור JSON
            with open("daily_results.json", "w", encoding="utf-8") as f:
                out = {tid: {k: v for k, v in d.items() if k != "raw"}
                       for tid, d in summary.items()}
                json.dump({"date": today, "summary": out}, f, ensure_ascii=False, indent=2)
            print(f"💾 נשמר ב-daily_results.json")

        except Exception as e:
            print(f"❌ {e}")
            try: page.screenshot(path="error.png")
            except: pass
        finally:
            ctx.close()
            browser.close()


def already_saved(date_str: str, terminal_id: str) -> bool:
    """בודק אם כבר יש רשומה ב-NOSBroadcast לאותו מסוף ותאריך"""
    if not B44_KEY:
        return False
    d, m, y = date_str.split("/")
    date_iso = f"{y}-{m}-{d}"
    try:
        r = requests.get(
            f"{B44_URL}/entities/NOSBroadcast",
            headers=B44_HDR,
            params={"query": json.dumps({
                "date": date_iso,
                "terminal_id": terminal_id,
                "status": "ok"
            }), "limit": 1},
            timeout=10
        )
        data = r.json()
        return len(data.get("entities", [])) > 0
    except:
        return False


def run_with_retry(test_date: str = None):
    """
    מריץ עם retry — ריצות ב-19:30, 20:00, 20:30, 21:00.
    ב-21:00 אם עדיין חסר → שולח התראה.
    """
    import time as time_module

    today = test_date or datetime.now().strftime("%d/%m/%Y")
    weekday = datetime.strptime(today, "%d/%m/%Y").weekday()

    if weekday == 5 and not test_date:
        print("🕍 שבת — אין ריצה")
        return

    # זמני ריצה: 19:30, 20:00, 20:30, 21:00
    run_times = ["19:30", "20:00", "20:30", "21:00"]
    max_attempts = len(run_times)

    for attempt in range(max_attempts):
        print("\n" + "="*55)
        print(f"🔄 ניסיון {attempt+1}/{max_attempts} — {today}")
        print("="*55)

        results = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=100)
            ctx  = browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="he-IL"
            )
            page = ctx.new_page()

            try:
                login(page)
                rows = get_all_shva(page, today)
                summary = process_rows(rows, today)

                for tid, data in summary.items():
                    results[tid] = data

            except Exception as e:
                print(f"❌ שגיאה: {e}")
            finally:
                ctx.close()
                browser.close()

        # ── בדוק מה חסר ──
        missing = []
        for tid, name in TERMINALS.items():
            if tid not in results or results[tid]["total"] == 0:
                missing.append((tid, name))

        # ── סיכום הניסיון ──
        print(f"\n📋 סיכום ניסיון {attempt+1} — {today}")
        for tid, data in results.items():
            if data["total"] > 0:
                print(f"  ✅ {data['name']:8s}: ₪{data['total']:>12,.2f}  ({data['transactions']} עסקאות)")

        for tid, name in missing:
            print(f"  ❌ {name:8s}: אין שידור עדיין")

        # ── שמור מה שיש ל-Base44 ──
        if B44_KEY:
            for tid, data in results.items():
                if data["total"] > 0 and not already_saved(today, tid):
                    save_to_base44(today, tid, data)
                elif data["total"] > 0:
                    print(f"  ℹ️  {data['name']} כבר קיים ב-Base44 — לא כותב שוב")

        # ── אם הכל טופל → סיים ──
        if not missing:
            print(f"✅ כל המסופים נסגרו! מסיים.")
            break

        # ── אם זה הניסיון האחרון → שלח התראה ──
        if attempt == max_attempts - 1:
            names = [name for _, name in missing]
            print(f"⚠️  21:00 — עדיין לא נסגרו: {', '.join(names)}")
            send_whatsapp_alert(today, [tid for tid, _ in missing])
            break

        # ── אחרת → המתן לניסיון הבא ──
        if not test_date:
            wait_minutes = 30
            print(f"⏳ ממתין {wait_minutes} דקות לניסיון הבא...")
            time_module.sleep(wait_minutes * 60)
        else:
            # במצב בדיקה — לא ממתינים
            print(f"🧪 מצב בדיקה — לא ממתין")
            break

    # שמור JSON
    with open("daily_results.json", "w", encoding="utf-8") as f:
        out = {}
        for tid, data in results.items() if results else {}.items():
            out[tid] = {k: v for k, v in data.items() if k != "raw"}
        json.dump({"date": today, "summary": out}, f, ensure_ascii=False, indent=2)
    print(f"💾 נשמר ב-daily_results.json")


if __name__ == "__main__":
    import sys
    if not PASSWORD:
        print("❌ חסרה NEWORDER_PASSWORD ב-.env"); exit(1)

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None

    if date_arg:
        # מצב בדיקה — תאריך ספציפי
        run(test_date=date_arg)
    else:
        # מצב אוטומטי — עם retry
        run_with_retry()
