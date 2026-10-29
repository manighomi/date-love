import os
import secrets
import html

import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, redirect, render_template_string, session, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL تنظیم نشده است")
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=10
    )


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id BIGSERIAL PRIMARY KEY,
                phone TEXT NOT NULL,
                consent BOOLEAN NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


HOME_HTML = """
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>یه قرار قشنگ ❤️</title>
<style>
*{box-sizing:border-box}
body{font-family:Tahoma,Arial;background:linear-gradient(135deg,#ffe0ec,#fff5f8);
display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;color:#55263b}
.card{background:white;padding:28px;border-radius:24px;box-shadow:0 12px 40px #9b416c22;
width:min(420px,90%);text-align:center}
h1{color:#d63384}
p{line-height:2}
input[type=tel]{width:100%;padding:14px;border:1px solid #e9b9cf;
border-radius:12px;font-size:16px;margin:12px 0}
label{display:block;text-align:right;line-height:1.9;font-size:14px}
button{background:#d63384;color:white;border:0;padding:14px 22px;border-radius:12px;
font-size:16px;width:100%;margin-top:16px;cursor:pointer}
</style>
</head>
<body>
<main class="card">
<h1>یه قرار قشنگ؟ ❤️</h1>
<p>بیایم یه روز قشنگ بسازیم!<br>
با هم انتخاب کنیم کجا بریم، چه ساعتی همدیگه رو ببینیم و چی بخوریم. 🌷</p>
<form action="/submit" method="post">
<input type="tel" name="phone" placeholder="شماره تماس" required
pattern="[0-9+() -]{7,20}" maxlength="20" autocomplete="tel">
<label><input type="checkbox" name="consent" required>
با ذخیره شماره تماس من برای هماهنگی این قرار موافقم.</label>
<button type="submit">ثبت پاسخ ❤️</button>
</form>
</main>
</body>
</html>
"""

THANKS_HTML = """
<!doctype html>
<html lang="fa" dir="rtl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ممنون ❤️</title></head>
<body style="font-family:Tahoma;text-align:center;padding:60px;background:#fff0f6;color:#7a2450">
<h1>پاسخت ثبت شد ❤️</h1>
<p>ممنون! امیدوارم یه قرار قشنگ داشته باشیم.</p>
<a href="/">بازگشت</a>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(HOME_HTML)


@app.post("/submit")
def submit():
    phone = request.form.get("phone", "").strip()
    consent = request.form.get("consent") == "on"

    if not phone or len(phone) > 20 or not consent:
        abort(400)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO responses (phone, consent) VALUES (%s, %s)",
            (phone, consent)
        )

    return render_template_string(THANKS_HTML)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not ADMIN_PASSWORD:
        return "رمز مدیریت در تنظیمات Render تعریف نشده است.", 503

    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session["admin_authenticated"] = True
            return redirect("/admin")
        return "رمز اشتباه است.", 401

    if not session.get("admin_authenticated"):
        return """
        <!doctype html>
        <html lang="fa" dir="rtl">
        <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body style="font-family:Tahoma;max-width:350px;margin:80px auto">
        <h2>ورود مدیر</h2>
        <form method="post">
        <input name="password" type="password" placeholder="رمز مدیریت" required>
        <button type="submit">ورود</button>
        </form>
        </body></html>
        """

    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, phone, consent, created_at
            FROM responses
            ORDER BY id DESC
            LIMIT 200
        """).fetchall()

    output = """
    <!doctype html><html lang="fa" dir="rtl">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>پنل مدیریت</title>
    <style>
    body{font-family:Tahoma;padding:16px;background:#fff5f8}
    .table-wrap{overflow-x:auto}
    table{border-collapse:collapse;width:100%;background:white}
    th,td{border:1px solid #ddd;padding:8px;text-align:right}
    </style></head><body>
    <h2>پاسخ‌های ثبت‌شده</h2><a href="/admin/logout">خروج</a>
    <div class="table-wrap"><table>
    <tr><th>شماره</th><th>تلفن</th><th>رضایت</th><th>زمان ثبت</th></tr>
    """

    for row in rows:
        phone = html.escape(str(row["phone"]))
        created = html.escape(str(row["created_at"]))
        consent = "بله" if row["consent"] else "خیر"
        output += (
            f"<tr><td>{row['id']}</td><td>{phone}</td>"
            f"<td>{consent}</td><td>{created}</td></tr>"
        )

    output += "</table></div></body></html>"
    return output


@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin")


# ساخت جدول هنگام شروع برنامه
init_db()
