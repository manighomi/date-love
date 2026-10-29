import os
import sqlite3
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

DB_PATH = os.environ.get("DB_PATH", "responses.db")

HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>یه آشنایی قشنگ ❤️</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: Tahoma, sans-serif;
  background: linear-gradient(135deg,#ffe0ec,#fff5f8,#ffc7dc);
  color: #631b3b;
}
.card {
  width: 100%;
  max-width: 540px;
  padding: 28px 22px;
  background: white;
  border-radius: 25px;
  box-shadow: 0 15px 45px #d88ba855;
}
h1 {
  text-align: center;
  color: #d81b60;
  font-size: 24px;
  line-height: 1.9;
}
.message {
  font-size: 16px;
  line-height: 2.3;
}
label {
  display: block;
  margin: 15px 0 9px;
  font-weight: bold;
  line-height: 2;
}
input[type="tel"] {
  width: 100%;
  padding: 15px;
  border: 1px solid #e9a9c2;
  border-radius: 12px;
  font-size: 16px;
  direction: ltr;
  text-align: left;
}
.consent {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  font-size: 13px;
  font-weight: normal;
}
button {
  width: 100%;
  padding: 16px 10px;
  border: 0;
  border-radius: 13px;
  color: white;
  background: linear-gradient(135deg,#ec407a,#c2185b);
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
}
.note {
  text-align: center;
  font-size: 12px;
  line-height: 2;
  color: #96667a;
}
.flash {
  padding: 10px;
  background: #fff0f5;
  border-radius: 10px;
}
</style>
</head>
<body>
<div class="card">
  <h1>🌹 یه سؤال ازت دارم، خانم خوشگله! ❤️</h1>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <p class="flash">{{ messages[0] }}</p>
    {% endif %}
  {% endwith %}

  <div class="message">
    <p>می‌دونی قشنگ‌ترین اتفاقی که می‌تونه برای یه روز معمولی بیفته چیه؟ 😌</p>

    <p>اینکه یه نفر وارد زندگیت بشه و بدون اینکه بفهمی، لبخند رو بیاره روی لبت... ❤️✨</p>

    <p>راستش، من دوست دارم اون یه نفر برای تو باشم! 😉💘</p>

    <p>حالا اگه تو هم بدت نمیاد بیشتر با هم آشنا بشیم، بیا این مرحله رو هم انجام بدیم... 🥹❤️</p>
  </div>

  <form method="POST" action="/submit">
    <label for="phone">📱 شماره موبایلت رو وارد کن تا بیشتر با هم در ارتباط باشیم:</label>

    <input
      id="phone"
      name="phone"
      type="tel"
      placeholder="مثلاً 09123456789"
      maxlength="20"
      required
    >

    <label class="consent">
      <input type="checkbox" name="consent" value="yes" required>
      <span>با رضایت خودم شماره‌ام را برای آشنایی در اختیار صاحب سایت قرار می‌دهم.</span>
    </label>

    <br>

    <button type="submit">💌 بزن بریم برای یه آشنایی قشنگ!</button>

    <p class="note">واردکردن شماره اختیاری است؛ فقط اگر خودت تمایل داری ادامه بده. ❤️</p>
  </form>
</div>
</body>
</html>
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)


@app.route("/submit", methods=["POST"])
def submit():
    phone = request.form.get("phone", "").strip()
    consent = request.form.get("consent")

    digits = "".join(c for c in phone if c.isdigit())

    if consent != "yes":
        flash("برای ادامه باید رضایت خودت را تأیید کنی.")
        return redirect(url_for("home"))

    if len(digits) < 8 or len(digits) > 15:
        flash("لطفاً شماره معتبر وارد کن.")
        return redirect(url_for("home"))

    init_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO responses (phone, created_at) VALUES (?, ?)",
            (phone, datetime.utcnow().isoformat() + "Z")
        )

    return """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <body style="font-family:Tahoma;text-align:center;padding:40px;background:#fff0f5;color:#a31550;line-height:2">
      <h1>ممنون از اعتمادت! ❤️🌹</h1>
      <p>اطلاعاتت ثبت شد.</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
