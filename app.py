from flask import Flask, render_template_string, request, redirect, jsonify, session, url_for
from flask_cors import CORS
import sqlite3
import json
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = "memora_demo_secret_2026"
CORS(app)

DATABASE = "memora.db"
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "1234"


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            caregiver TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT NOT NULL,
            photo TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            task_time TEXT,
            category TEXT DEFAULT 'Daily',
            done INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            reminder_time TEXT,
            done INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            done INTEGER DEFAULT 0
        )
    """)

    if conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0] == 0:
        conn.execute("""
            INSERT INTO patient (name, age, gender, phone, caregiver)
            VALUES (?, ?, ?, ?, ?)
        """, ("Meenakshi", 70, "Female", "8056962028", "Anitha"))

    if conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0:
        conn.execute("""
            INSERT INTO memories (category, title, details)
            VALUES (?, ?, ?)
        """, ("Person", "Daughter", "Anitha"))
        conn.execute("""
            INSERT INTO memories (category, title, details)
            VALUES (?, ?, ?)
        """, ("Food", "Favourite Food", "Idli"))
        conn.execute("""
            INSERT INTO memories (category, title, details)
            VALUES (?, ?, ?)
        """, ("Place", "Favourite Place", "Village Home"))

    if conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
        for title, tm, cat in [
            ("Breakfast", "09:00", "Routine"),
            ("Memory Activity", "10:30", "Cognitive"),
            ("Lunch", "13:00", "Routine"),
            ("Evening Walk", "17:00", "Exercise"),
        ]:
            conn.execute(
                "INSERT INTO tasks (title, task_time, category) VALUES (?, ?, ?)",
                (title, tm, cat)
            )

    if conn.execute("SELECT COUNT(*) FROM reminders").fetchone()[0] == 0:
        for title, tm in [
            ("Have a glass of water", "08:30"),
            ("Take medicine", "14:00"),
            ("Music time", "17:30"),
        ]:
            conn.execute(
                "INSERT INTO reminders (title, reminder_time) VALUES (?, ?)",
                (title, tm)
            )

    conn.commit()
    conn.close()


def get_patient():
    conn = db()
    row = conn.execute("SELECT * FROM patient LIMIT 1").fetchone()
    conn.close()
    return row


# =========================================================
# COMMON HTML / CSS
# =========================================================

BASE_CSS = """
:root{
    --indigo:#4943a5;
    --indigo-dark:#37327f;
    --cream:#faf8f2;
    --paper:#fffefb;
    --text:#273047;
    --muted:#68738a;
    --green:#08b77b;
    --mint:#dceee9;
    --gold:#f3b642;
    --peach:#f9e7c5;
    --line:#e5dfd4;
    --shadow:0 10px 30px rgba(50,45,80,.08);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
    margin:0;
    font-family:Arial,Helvetica,sans-serif;
    background:var(--cream);
    color:var(--text);
}
button,input,select,textarea{font:inherit}
button{cursor:pointer}
a{text-decoration:none;color:inherit}
.layout{display:flex;min-height:100vh}
.sidebar{
    width:270px;background:#fffdfa;border-right:1px solid var(--line);
    padding:22px 18px;position:fixed;left:0;top:0;bottom:0;z-index:10;
}
.brand{display:flex;align-items:center;gap:14px;margin-bottom:30px}
.brand-icon{
    width:48px;height:48px;border-radius:16px;background:var(--indigo);
    color:white;display:grid;place-items:center;font-size:24px;
}
.brand h1{margin:0;font-family:Georgia,serif;font-size:28px;letter-spacing:-1px}
.brand p{margin:4px 0 0;color:var(--muted);font-size:12px;letter-spacing:3px}
.profile-mini{
    background:#e7f2ee;border-radius:20px;padding:14px;margin-bottom:24px;
    display:flex;gap:12px;align-items:center
}
.avatar{width:54px;height:54px;border-radius:17px;background:#f0b548;display:grid;place-items:center;font-weight:bold;font-size:22px}
.profile-mini strong{display:block}.profile-mini span{color:var(--muted);font-size:14px}
.nav a{
    display:flex;align-items:center;gap:13px;padding:14px 15px;border-radius:30px;
    color:#657087;margin:4px 0;font-weight:bold
}
.nav a:hover,.nav a.active{background:var(--indigo);color:white}
.sidebar-bottom{position:absolute;bottom:20px;left:18px;right:18px}
.main{margin-left:270px;width:calc(100% - 270px);min-height:100vh}
.topbar{
    height:65px;border-bottom:1px solid var(--line);background:#fffdfa;
    display:flex;align-items:center;justify-content:space-between;padding:0 28px;
    position:sticky;top:0;z-index:5
}
.status-online{display:flex;align-items:center;gap:10px;color:var(--muted);font-weight:bold}
.dot{width:10px;height:10px;border-radius:50%;background:var(--green)}
.lang{
    border:1px solid var(--line);border-radius:25px;padding:11px 16px;
    background:white;color:var(--text);font-weight:bold
}
.content{padding:30px 50px;max-width:1500px;margin:auto}
.hero{
    background:linear-gradient(110deg,#4943a5,#514ab0);
    color:white;border-radius:30px;padding:36px 44px;min-height:220px;
    display:flex;align-items:center;justify-content:space-between;gap:30px;
    box-shadow:var(--shadow)
}
.hero h2{font-family:Georgia,serif;font-size:38px;margin:0 0 12px}
.hero p{font-size:17px;line-height:1.6;max-width:720px;color:#ecebff}
.hero-actions{display:flex;gap:12px;flex-wrap:wrap}
.btn{
    display:inline-flex;align-items:center;justify-content:center;gap:8px;
    border:0;border-radius:14px;padding:13px 19px;font-weight:bold;
    background:var(--indigo);color:white;min-height:46px
}
.btn:hover{background:var(--indigo-dark)}
.btn-light{background:white;color:var(--indigo)}
.btn-mint{background:var(--mint);color:#285b53}
.btn-gold{background:var(--peach);color:#5d4b25}
.btn-outline{background:white;color:var(--indigo);border:1px solid #d8d2c7}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:24px;margin-top:26px}
.panel{
    background:var(--paper);border:1px solid var(--line);border-radius:25px;
    padding:25px;box-shadow:var(--shadow)
}
.col-4{grid-column:span 4}.col-5{grid-column:span 5}.col-6{grid-column:span 6}
.col-7{grid-column:span 7}.col-8{grid-column:span 8}.col-12{grid-column:span 12}
.eyebrow{font-size:12px;letter-spacing:2px;color:#6f788b;text-transform:uppercase}
.panel h2,.panel h3{font-family:Georgia,serif;margin:7px 0 18px}
.quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.quick{
    padding:22px;border-radius:20px;min-height:115px;display:flex;
    flex-direction:column;justify-content:space-between;border:1px solid #eee9df
}
.quick.mint{background:#dceee9}.quick.peach{background:#f9e7c5}.quick.soft{background:#eeece7}
.reminder-row,.task-row,.status-row{
    display:flex;align-items:center;justify-content:space-between;gap:15px;
    padding:15px 0;border-bottom:1px solid var(--line)
}
.reminder-row:last-child,.task-row:last-child,.status-row:last-child{border-bottom:0}
.left{display:flex;align-items:center;gap:12px}
.badge{width:12px;height:12px;border-radius:50%;background:var(--gold)}
.badge.green{background:var(--green)}
.time{color:#68738a;font-family:monospace}
.done{text-decoration:line-through;color:#7a8494}
.page-title{font-family:Georgia,serif;font-size:38px;margin:0 0 8px}
.page-sub{color:var(--muted);margin:0 0 25px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.field{display:flex;flex-direction:column;gap:7px}.field.full{grid-column:1/-1}
.field label{font-weight:bold;font-size:14px}
.field input,.field select,.field textarea{
    width:100%;padding:13px 14px;border:1px solid #dcd6cc;border-radius:12px;
    background:white;outline:none
}
.field textarea{min-height:100px;resize:vertical}
.notice{padding:13px 15px;border-radius:12px;background:#e8f4ef;color:#276357;margin:15px 0}
.error{padding:13px 15px;border-radius:12px;background:#fff0ed;color:#9a4034;margin:15px 0}
.center{text-align:center}
.meter{height:18px;background:#ebe8e1;border-radius:30px;overflow:hidden}
.meter-fill{height:100%;background:var(--indigo);border-radius:30px;transition:width .4s}
.big-number{font-size:48px;font-weight:bold;color:var(--indigo)}
.feature-card{
    padding:22px;border:1px solid var(--line);border-radius:20px;background:white;
    min-height:175px;display:flex;flex-direction:column;justify-content:space-between
}
.feature-card h3{font-family:Georgia,serif;margin:0 0 8px}
.feature-card p{color:var(--muted);line-height:1.5}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.memory-photo{
    width:100%;height:160px;object-fit:cover;border-radius:15px;margin-bottom:12px
}
.placeholder-photo{
    width:100%;height:160px;border-radius:15px;background:#eeece7;display:grid;
    place-items:center;font-size:42px;margin-bottom:12px
}
.game{
    border:1px solid var(--line);border-radius:20px;padding:22px;background:#fff;
    margin-bottom:18px
}
.game-options{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.game-options button{min-height:60px;border:1px solid #ddd6cc;border-radius:14px;background:#f5f2eb}
.game-options button:hover{background:#e5efe9}
.result{font-weight:bold;margin-top:15px;min-height:25px}
.exercise-animation{
    width:190px;height:190px;margin:15px auto;border-radius:50%;
    background:#dceee9;display:grid;place-items:center;font-size:75px;
    animation:breathe 5s ease-in-out infinite
}
@keyframes breathe{0%,100%{transform:scale(.82)}50%{transform:scale(1.08)}}
.sleep-ring{
    width:190px;height:190px;border-radius:50%;margin:10px auto;
    display:grid;place-items:center;background:conic-gradient(var(--indigo) 0 78%,#e9e5dc 78% 100%)
}
.sleep-inner{width:140px;height:140px;border-radius:50%;background:white;display:grid;place-items:center;text-align:center}
.location-box{background:#eef4f1;padding:18px;border-radius:18px}
.login-wrap{min-height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#f5f2ff,#f8f4e9);padding:20px}
.login-card{width:min(450px,100%);background:white;border:1px solid var(--line);border-radius:30px;padding:40px;box-shadow:var(--shadow)}
.login-logo{text-align:center}.login-logo .brand-icon{margin:auto}
.toast{
    position:fixed;right:24px;bottom:24px;background:#283044;color:white;
    padding:14px 18px;border-radius:14px;display:none;z-index:100
}
.footer{text-align:center;color:#7c8493;padding:35px}
.small{font-size:13px;color:var(--muted)}

.selected {
    transform: scale(1.03);
    border: 3px solid #4f46e5;
    background: #eef2ff !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.selected small {
    display: block;
    font-size: 12px;
    margin-top: 4px;
}

@media(max-width:1000px){
    .sidebar{width:220px}.main{margin-left:220px;width:calc(100% - 220px)}
    .content{padding:25px}.cards{grid-template-columns:1fr 1fr}
}
@media(max-width:760px){
    .sidebar{position:static;width:100%;height:auto}.sidebar-bottom{position:static;margin-top:20px}
    .layout{display:block}.main{margin-left:0;width:100%}.topbar{position:static}
    .content{padding:18px}.grid{grid-template-columns:1fr}.col-4,.col-5,.col-6,.col-7,.col-8,.col-12{grid-column:span 1}
    .hero{padding:25px;display:block}.hero h2{font-size:30px}.hero-actions{margin-top:20px}
    .form-grid,.quick-grid,.game-options,.cards{grid-template-columns:1fr}
}
"""


def page(title, body, active="today", patient=None):
    patient = patient or get_patient()
    initial = (patient["name"] or "M")[0].upper()
    nav = f"""
    <aside class="sidebar">
      <a class="brand" href="/">
        <div class="brand-icon">♡</div>
        <div><h1>MEMORA</h1><p>TOGETHER, EACH DAY</p></div>
      </a>
      <div class="profile-mini">
        <div class="avatar">{initial}</div>
        <div><strong>{patient['name']}</strong><span>Your gentle space</span></div>
      </div>
      <nav class="nav">
        <a class="{'active' if active=='today' else ''}" href="/">⌂ &nbsp; Today</a>
        <a class="{'active' if active=='assistant' else ''}" href="/assistant">♧ &nbsp; Talk to MEMORA</a>
        <a class="{'active' if active=='memories' else ''}" href="/pin">▣ &nbsp; Memories</a>
        <a class="{'active' if active=='routine' else ''}" href="/routine">◷ &nbsp; My routine</a>
        <a class="{'active' if active=='reminders' else ''}" href="/reminders">♧ &nbsp; Reminders</a>
        <a class="{'active' if active=='activities' else ''}" href="/activities">♧ &nbsp; Activities</a>
        <a class="{'active' if active=='exercise' else ''}" href="/exercise">♧ &nbsp; Exercise & Yoga</a>
        <a class="{'active' if active=='sleep' else ''}" href="/sleep">◔ &nbsp; Deep Sleep</a>
        <a class="{'active' if active=='location' else ''}" href="/location">⌖ &nbsp; Location Finder</a>
        <a class="{'active' if active=='caregiver' else ''}" href="/caregiver">♙ &nbsp; Caregiver</a>
      </nav>
      <div class="sidebar-bottom">
        <a class="nav" href="/settings">⚙ &nbsp; Settings</a>
      </div>
    </aside>
    """
    return f"""<!DOCTYPE html><html><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>{title} — MEMORA</title><style>{BASE_CSS}</style></head><body>
    <div class="layout">{nav}<main class="main">
      <div class="topbar"><div class="status-online"><span class="dot"></span> A quiet place for today</div>
      <div style="display:flex;gap:18px;align-items:center"><span class="small">● Online</span>
      <span class="lang">文 &nbsp; English ▾</span> ⚙</div></div>
      <section class="content">{body}</section>
      <div class="footer">MEMORA © 2026 • A supportive prototype for everyday assistance</div>
    </main></div>
    <div id="toast" class="toast"></div>
    <script>
    function toast(msg){{const t=document.getElementById('toast');t.innerText=msg;t.style.display='block';setTimeout(()=>t.style.display='none',2200)}}
    </script>
    </body></html>"""


# =========================================================
# LOGIN / START
# =========================================================

LOGIN_HTML = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0"><title>MEMORA Login</title>
<style>{BASE_CSS}</style></head><body>
<div class="login-wrap"><div class="login-card">
<div class="login-logo"><div class="brand-icon">♡</div>
<h1 style="font-family:Georgia,serif;font-size:38px;margin:14px 0 4px">MEMORA</h1>
<p style="letter-spacing:3px;color:#68738a">TOGETHER, EACH DAY</p></div>
<h2 style="font-family:Georgia,serif;margin-top:30px">Welcome back</h2>
<p class="page-sub">A calm digital assistant for memories, routines and daily activities.</p>
<form method="POST" action="/login">
<div class="field"><label>Username</label><input name="username" placeholder="Enter username" required></div>
<div class="field" style="margin-top:15px"><label>Password / PIN</label><input type="password" name="password" placeholder="Enter password" required></div>
<button class="btn" style="width:100%;margin-top:20px">Start MEMORA →</button>
</form>
<p class="small center" style="margin-top:18px">Prototype login: <b>admin</b> / <b>1234</b></p>
</div></div></body></html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == DEMO_USERNAME and request.form.get("password") == DEMO_PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        return redirect("/login?error=1")
    return LOGIN_HTML


def require_login():
    return session.get("logged_in") is True

@app.route("/select-patient", methods=["GET", "POST"])
def select_patient():
    if not require_login():
        return redirect("/login")

    conn = db()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        session["patient_id"] = int(patient_id)
        conn.close()
        return redirect("/")

    patients = conn.execute(
        "SELECT * FROM patient ORDER BY id"
    ).fetchall()

    conn.close()

    options = ""

    for p in patients:
        options += f"""
        <button class="patient-option" type="submit" name="patient_id" value="{p['id']}">
            <div class="avatar">{p['name'][0].upper()}</div>
            <div>
                <h3>{p['name']}</h3>
                <p>Age {p['age']} • Caregiver: {p['caregiver']}</p>
            </div>
        </button>
        """

    body = f"""
    <h1 class="page-title">Select Patient</h1>
    <p class="page-sub">Choose the person whose MEMORA space you want to open.</p>

    <div class="panel">
        <div class="patient-list">
            <form method="POST">
                {options}
            </form>
        </div>
    </div>
    """

    return page("Select Patient", body, "today")


# =========================================================
# HOME DASHBOARD
# =========================================================

@app.route("/")
def home():
    if not require_login():
        return redirect("/login")

    p = get_patient()
    conn = db()
    reminders = conn.execute("SELECT * FROM reminders ORDER BY reminder_time LIMIT 5").fetchall()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY task_time LIMIT 6").fetchall()
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE done=1").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    percent = int(done / total * 100) if total else 0

    reminder_html = "".join(
        f"""<div class="reminder-row">
        <div class="left"><span class="badge {'green' if r['done'] else ''}"></span>
        <span class="{'done' if r['done'] else ''}">{r['title']}</span></div>
        <span class="time">{r['reminder_time']}</span></div>""" for r in reminders
    )

    task_html = "".join(
        f"""<div class="task-row">
        <div><b class="{'done' if t['done'] else ''}">{t['title']}</b>
        <div class="small">{t['category']}</div></div>
        <span class="time">{t['task_time']}</span></div>""" for t in tasks
    )

    body = f"""
    <div class="hero">
      <div>
        <div class="eyebrow" style="color:#dcd9ff">TODAY • {datetime.now().strftime('%d %b %Y')}</div>
        <h2>Good morning, {p['name']}.</h2>
        <p>You can ask me about a person, your next reminder, or an activity. You can also type instead.</p>
        <div class="hero-actions">
          <a class="btn btn-light" href="/assistant">🎙 Talk to MEMORA →</a>
          <a class="btn" style="background:#625cc0" href="/routine">View today's routine</a>
        </div>
      </div>
      <div style="text-align:center;min-width:180px"><div class="big-number" style="color:white">{percent}%</div>
      <div style="color:#ddd9ff">today's progress</div></div>
    </div>

    <div class="grid">
      <div class="panel col-7">
        <div class="eyebrow">QUICK ACTIONS</div><h2>Easy to reach</h2>
        <div class="quick-grid">
          <a class="quick mint" href="/assistant"><span>💬</span><b>Ask a question →</b></a>
          <a class="quick soft" href="/pin"><span>▣</span><b>Open memories →</b></a>
          <a class="quick peach" href="/activities"><span>🧠</span><b>Try an activity →</b></a>
          <a class="quick" href="/reminders"><span>♧</span><b>See reminders →</b></a>
        </div>
      </div>
      <div class="panel col-5">
        <div class="eyebrow">TODAY'S REMINDERS</div><h2>{len(reminders)} gentle prompts</h2>
        {reminder_html}
        <a class="btn btn-outline" style="margin-top:15px" href="/reminders">Manage reminders →</a>
      </div>
      <div class="panel col-6"><div class="eyebrow">MY ROUTINE</div><h2>Today's plan</h2>{task_html}
      <a class="btn" href="/routine" style="margin-top:15px">Open routine</a></div>
      <div class="panel col-6"><div class="eyebrow">YOUR SPACE</div><h2>MEMORA features</h2>
        <div class="cards" style="grid-template-columns:1fr 1fr">
          <a class="feature-card" href="/exercise"><h3>🌿 Exercise</h3><p>Gentle movement and yoga breathing.</p></a>
          <a class="feature-card" href="/sleep"><h3>🌙 Deep Sleep</h3><p>Simple sleep meter and calming mode.</p></a>
          <a class="feature-card" href="/location"><h3>📍 Location Finder</h3><p>Find current location and set an alarm.</p></a>
          <a class="feature-card" href="/activities"><h3>🎮 Games</h3><p>Memory, GK and attention activities.</p></a>
        </div>
      </div>
    </div>
    """
    return page("Today", body, "today", p)


# =========================================================
# PATIENT PROFILE
# =========================================================

@app.route("/patient", methods=["GET", "POST"])
def patient():
    if not require_login():
        return redirect("/login")
    if request.method == "POST":
        conn = db()
        conn.execute("""UPDATE patient SET name=?, age=?, gender=?, phone=?, caregiver=? WHERE id=1""",
                     (request.form["name"], request.form["age"], request.form["gender"],
                      request.form["phone"], request.form["caregiver"]))
        conn.commit(); conn.close()
        return redirect("/patient?saved=1")
    p = get_patient()
    body = f"""
    <h1 class="page-title">Patient Profile</h1><p class="page-sub">Keep the important basic details together.</p>
    { '<div class="notice">✓ Patient profile saved.</div>' if request.args.get('saved') else '' }
    <div class="panel">
    <form method="POST" class="form-grid">
      <div class="field"><label>Name</label><input name="name" value="{p['name']}" required></div>
      <div class="field"><label>Age</label><input type="number" name="age" value="{p['age']}"></div>
      <div class="field"><label>Gender</label><input name="gender" value="{p['gender']}"></div>
      <div class="field"><label>Phone</label><input name="phone" value="{p['phone']}"></div>
      <div class="field full"><label>Caregiver</label><input name="caregiver" value="{p['caregiver']}"></div>
      <div class="field full"><button class="btn">Save Profile</button></div>
    </form></div>
    """
    return page("Patient Profile", body, "today", p)


# =========================================================
# PIN + MEMORIES + PHOTOS
# =========================================================

PIN_PAGE = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEMORA PIN</title><style>{BASE_CSS}</style></head><body>
<div class="login-wrap"><div class="login-card center">
<div class="brand-icon" style="margin:auto">🔐</div><h1 style="font-family:Georgia,serif">Private Memories</h1>
<p class="page-sub">Enter your 4-digit PIN to open the personal memory bank.</p>
<div id="msg"></div><input id="pin" type="password" inputmode="numeric" maxlength="4" placeholder="Enter PIN" style="text-align:center;font-size:24px;width:100%;padding:14px;border:1px solid #ddd;border-radius:12px">
<button class="btn" onclick="unlock()" style="width:100%;margin-top:15px">Unlock Memories</button>
<a class="btn btn-outline" href="/" style="width:100%;margin-top:10px">Back</a>
<script>
function unlock(){{
 let p=document.getElementById('pin').value;
 let m=document.getElementById('msg');
 if(p!=='1234'){{m.innerHTML='<div class="error">Incorrect PIN. Try again.</div>';return;}}
 fetch('/verify-pin',{{method:'POST'}}).then(r=>r.json()).then(d=>{{if(d.success) location.href='/memories';}});
}}
</script></div></div></body></html>"""


@app.route("/pin")
def pin():
    if not require_login():
        return redirect("/login")
    return PIN_PAGE


@app.route("/verify-pin", methods=["POST"])
def verify_pin():
    if not require_login():
        return jsonify({"success": False}), 401
    session["pin_verified"] = True
    return jsonify({"success": True})


@app.route("/memories", methods=["GET", "POST"])
def memories():
    if not require_login():
        return redirect("/login")

    conn = db()

    # Demo: currently logged-in patient is Meenakshi (patient ID 1)
    patient_id = 1

    if request.method == "POST":
        photo = ""
        uploaded = request.files.get("photo")

        if uploaded and uploaded.filename:
            raw = uploaded.read()
            if len(raw) <= 2_500_000:
                mime = uploaded.mimetype or "image/jpeg"
                photo = "data:" + mime + ";base64," + base64.b64encode(raw).decode("utf-8")

        conn.execute(
            """INSERT INTO memories(category,title,details,photo,patient_id)
               VALUES(?,?,?,?,?)""",
            (
                request.form["category"],
                request.form["title"],
                request.form["details"],
                photo,
                patient_id
            )
        )
        conn.commit()

    rows = conn.execute(
        "SELECT * FROM memories WHERE patient_id=? ORDER BY id DESC",
        (patient_id,)
    ).fetchall()

    conn.close()

    cards = ""

    for m in rows:
        photo = m["photo"] if "photo" in m.keys() else ""

        pic = (
            f'<img class="memory-photo" src="{photo}">'
            if photo
            else '<div class="placeholder-photo">🖼</div>'
        )

        cards += f"""
        <div class="feature-card">
            {pic}
            <div>
                <div class="small">{m["category"]}</div>
                <h3>{m["title"]}</h3>
                <p>{m["details"]}</p>
            </div>
        </div>
        """

    body = f"""
    <h1 class="page-title">Personal Memory Bank</h1>
    <p class="page-sub">Memories, people, places and familiar moments.</p>

    <div class="grid">
        <div class="panel col-7">
            <div class="eyebrow">MEMORIES</div>
            <h2>{len(rows)} saved memories</h2>
            <div class="memory-grid">
                {cards}
            </div>
        </div>

        <div class="panel col-5">
            <div class="eyebrow">ADD MEMORY</div>
            <h2>Save a familiar moment</h2>

            <form method="POST" enctype="multipart/form-data">
                <div class="field">
                    <label>Category</label>
                    <select name="category">
                        <option>Person</option>
                        <option>Place</option>
                        <option>Food</option>
                        <option>Activity</option>
                        <option>Important Memory</option>
                    </select>
                </div>

                <div class="field">
                    <label>Title</label>
                    <input name="title" placeholder="Daughter" required>
                </div>

                <div class="field">
                    <label>Details</label>
                    <input name="details" placeholder="Anitha" required>
                </div>

                <div class="field">
                    <label>Photo</label>
                    <input type="file" name="photo" accept="image/*">
                </div>

                <button class="btn" style="width:100%;margin-top:15px">
                    ＋ Save Memory
                </button>
            </form>
        </div>
    </div>
    """

    return page("Memories", body, "memories", get_patient())

# =========================================================
# VOICE ASSISTANT + REGIONAL LANGUAGES
# =========================================================

ASSISTANT_PAGE = f"""
<div class="grid">
<div class="panel col-7">
<div class="eyebrow">VOICE INTERFACE</div><h1 class="page-title">Talk to MEMORA</h1>
<p class="page-sub">Ask about a person, memory, reminder, activity or the patient's name. You can also type.</p>
<div style="display:flex;gap:12px;flex-wrap:wrap">
<button class="btn" onclick="listen()">🎙 Start listening</button>
<select id="language" class="lang">
<option value="en-IN">English</option><option value="ta-IN">தமிழ் Tamil</option>
<option value="hi-IN">हिन्दी Hindi</option><option value="kn-IN">ಕನ್ನಡ Kannada</option>
</select>
</div>
<div id="question" class="panel" style="margin-top:20px;background:#f5f3ff">Your question will appear here.</div>
<div id="answer" class="panel" style="margin-top:15px;background:#dceee9;font-size:19px">MEMORA is ready to help.</div>
<div style="display:flex;gap:10px;margin-top:15px">
<input id="typed" placeholder="Type your question..." style="flex:1;padding:14px;border:1px solid #ddd;border-radius:12px">
<button class="btn" onclick="askTyped()">Ask →</button></div>
<p class="small" style="margin-top:15px">Example: “Who is my daughter?” • “What is my favourite food?” • “What is my next reminder?”</p>
</div>
<div class="panel col-5">
<div class="eyebrow">MULTILINGUAL</div><h2>Gentle replies</h2>
<div class="status-row"><span>English</span><b>Ready</b></div>
<div class="status-row"><span>தமிழ்</span><b>Ready</b></div>
<div class="status-row"><span>हिन्दी</span><b>Ready</b></div>
<div class="status-row"><span>ಕನ್ನಡ</span><b>Ready</b></div>
<div class="notice">The browser handles speech recognition and spoken replies. Chrome works best for this prototype.</div>
</div></div>
<script>
function show(text){{
 document.getElementById('answer').innerText='MEMORA: '+text;
 let u=new SpeechSynthesisUtterance(text);u.lang=document.getElementById('language').value;u.rate=.9;
 speechSynthesis.cancel();speechSynthesis.speak(u);
}}
function askText(text){{
 document.getElementById('question').innerText='You: '+text;
 fetch('/ask',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{question:text,language:document.getElementById('language').value}})}})
 .then(r=>r.json()).then(d=>show(d.answer));
}}
function askTyped(){{let t=document.getElementById('typed').value.trim();if(t)askText(t)}}
function listen(){{
 if(!('webkitSpeechRecognition' in window)){{alert('Voice recognition is not supported here. Use Google Chrome.');return;}}
 let r=new webkitSpeechRecognition();r.lang=document.getElementById('language').value;r.continuous=false;r.interimResults=false;
 document.getElementById('answer').innerText='Listening...';r.start();
 r.onresult=e=>askText(e.results[0][0].transcript);
 r.onerror=()=>document.getElementById('answer').innerText='Please try again.';
}}
</script>
"""


@app.route("/assistant")
def assistant():
    if not require_login():
        return redirect("/login")
    return page("Talk to MEMORA", ASSISTANT_PAGE, "assistant", get_patient())


@app.route("/ask", methods=["POST"])
def ask():
    if not require_login():
        return jsonify({"answer": "Please log in first."}), 401
    data = request.get_json() or {}
    q = data.get("question", "").lower().strip()
    lang = data.get("language", "en-IN")

    conn = db()
    memories = conn.execute("SELECT * FROM memories").fetchall()
    reminders = conn.execute("SELECT * FROM reminders ORDER BY reminder_time").fetchall()
    patient = conn.execute("SELECT * FROM patient LIMIT 1").fetchone()
    conn.close()

    answer = None

    if any(x in q for x in ["daughter", "son", "mother", "father", "wife", "husband", "friend"]):
        for m in memories:
            if any(x in (m["title"] + " " + m["details"]).lower() for x in ["daughter","son","mother","father","wife","husband","friend"]):
                answer = f"Your {m['title'].lower()} is {m['details']}."
                break

    if answer is None and any(x in q for x in ["favourite food","favorite food","food","eat"]):
        for m in memories:
            if m["category"].lower() == "food":
                answer = f"Your favourite food is {m['details']}."
                break

    if answer is None and ("next reminder" in q or "reminder" in q):
        if reminders:
            answer = f"Your next reminder is {reminders[0]['title']} at {reminders[0]['reminder_time']}."

    if answer is None and ("my name" in q or "your name" in q or q == "name"):
        answer = f"Your name is {patient['name']}."

    if answer is None:
        for m in memories:
            if m["title"].lower() in q or m["details"].lower() in q:
                answer = f"{m['title']} is {m['details']}."
                break

    if answer is None:
        answer = "I don't have that information in my memory bank yet."

    translations = {
        "ta-IN": {
            "Your name is": "உங்கள் பெயர்",
            "Your next reminder is": "உங்கள் அடுத்த நினைவூட்டல்",
            "I don't have that information in my memory bank yet.": "அந்த தகவல் இன்னும் என் நினைவகத்தில் இல்லை."
        },
        "hi-IN": {
            "Your name is": "आपका नाम है",
            "I don't have that information in my memory bank yet.": "यह जानकारी अभी मेरी मेमोरी में नहीं है।"
        },
        "kn-IN": {
            "Your name is": "ನಿಮ್ಮ ಹೆಸರು",
            "I don't have that information in my memory bank yet.": "ಈ ಮಾಹಿತಿ ಇನ್ನೂ ನನ್ನ ಮೆಮೊರಿಯಲ್ಲಿ ಇಲ್ಲ."
        }
    }
    if lang != "en-IN" and answer in translations.get(lang, {}):
        answer = translations[lang][answer]

    return jsonify({"answer": answer})


# =========================================================
# ROUTINE / TASKS
# =========================================================

@app.route("/routine", methods=["GET", "POST"])
def routine():
    if not require_login(): return redirect("/login")
    conn = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            conn.execute("INSERT INTO tasks(title,task_time,category) VALUES(?,?,?)",
                         (request.form["title"], request.form["task_time"], request.form.get("category","Daily")))
        elif action == "done":
            conn.execute("UPDATE tasks SET done=1 WHERE id=?", (request.form["id"],))
        conn.commit()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY task_time").fetchall()
    conn.close()
    rows = "".join(f"""<div class="task-row"><div class="left"><span class="badge {'green' if t['done'] else ''}"></span>
    <div><b class="{'done' if t['done'] else ''}">{t['title']}</b><div class="small">{t['category']}</div></div></div>
    <span class="time">{t['task_time']}</span>
    {'<span>✓ Done</span>' if t['done'] else f'<form method="POST"><input type="hidden" name="action" value="done"><input type="hidden" name="id" value="{t["id"]}"><button class="btn" style="min-height:36px;padding:8px 12px">Mark done</button></form>'}
    </div>""" for t in tasks)
    p = get_patient()
    body = f"""<h1 class="page-title">My Routine</h1><p class="page-sub">Daily tasks with simple completion tracking.</p>
    <div class="grid"><div class="panel col-7"><div class="eyebrow">TODAY'S PLAN</div><h2>Gentle steps</h2>{rows}</div>
    <div class="panel col-5"><h2>Add task</h2><form method="POST">
    <input type="hidden" name="action" value="add"><div class="field"><label>Task</label><input name="title" placeholder="Example: Call family" required></div>
    <div class="field" style="margin-top:12px"><label>Time</label><input type="time" name="task_time" required></div>
    <div class="field" style="margin-top:12px"><label>Category</label><select name="category"><option>Daily</option><option>Routine</option><option>Exercise</option><option>Appointment</option></select></div>
    <button class="btn" style="width:100%;margin-top:15px">＋ Add Task</button></form></div></div>"""
    return page("Routine", body, "routine", get_patient())


# =========================================================
# REMINDERS + NOTIFICATIONS
# =========================================================

@app.route("/reminders", methods=["GET", "POST"])
def reminders():
    if not require_login(): return redirect("/login")
    conn = db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            conn.execute("INSERT INTO reminders(title,reminder_time) VALUES(?,?)",
                         (request.form["title"], request.form["reminder_time"]))
        elif action == "done":
            conn.execute("UPDATE reminders SET done=1 WHERE id=?", (request.form["id"],))
        conn.commit()
    rows = conn.execute("SELECT * FROM reminders ORDER BY reminder_time").fetchall()
    conn.close()
    reminder_rows = "".join(f"""<div class="reminder-row"><div class="left"><span class="badge {'green' if r['done'] else ''}"></span>
    <span class="{'done' if r['done'] else ''}">{r['title']}</span></div><span class="time">{r['reminder_time']}</span>
    {'<span>✓ Done</span>' if r['done'] else f'<form method="POST"><input type="hidden" name="action" value="done"><input type="hidden" name="id" value="{r["id"]}"><button class="btn" style="min-height:35px;padding:7px 12px">Done</button></form>'}</div>""" for r in rows)
    body = f"""<h1 class="page-title">Reminders & Notifications</h1><p class="page-sub">Gentle prompts for water, medicine, activities and custom tasks.</p>
    <div class="grid"><div class="panel col-7"><div class="eyebrow">TODAY'S REMINDERS</div><h2>{len(rows)} gentle prompts</h2>{reminder_rows}</div>
    <div class="panel col-5"><h2>Add reminder</h2><form method="POST"><input type="hidden" name="action" value="add">
    <div class="field"><label>Reminder</label><input name="title" placeholder="Drink water" required></div>
    <div class="field" style="margin-top:12px"><label>Time</label><input type="time" name="reminder_time" required></div>
    <button class="btn" style="width:100%;margin-top:15px">＋ Add Reminder</button></form>
    <button class="btn btn-mint" style="width:100%;margin-top:12px" onclick="notifyMe()">🔔 Enable browser notifications</button>
    <p class="small">Notifications require browser permission. This prototype does not send notifications when the browser is completely closed.</p>
    </div></div>
    <script>
function notifyMe(){{
    if(!('Notification' in window)){{
        alert('Notifications are not supported here.');
        return;
    }}

    Notification.requestPermission().then(p=>{{
        if(p==='granted'){{
            new Notification('MEMORA', {{
                body: 'Notifications are enabled.'
            }});

            speakReminder('Notifications are enabled.');
        }}
    }});
}}

function speakReminder(message){{
    if('speechSynthesis' in window){{
        const speech = new SpeechSynthesisUtterance(message);
        speech.rate = 0.9;
        speech.pitch = 1;
        window.speechSynthesis.speak(speech);
    }}
}}

function checkReminders(){{
    const now = new Date();
    const currentTime =
        String(now.getHours()).padStart(2,'0') + ':' +
        String(now.getMinutes()).padStart(2,'0');

    const reminders = {json.dumps([dict(r) for r in rows])};

    reminders.forEach(r => {{
        if(!r.done && r.reminder_time === currentTime){{
            const message = "It's time for " + r.title;

            if('Notification' in window && Notification.permission === 'granted'){{
                new Notification('MEMORA Reminder', {{
                    body: message
                }});
            }}

            speakReminder(message);
        }}
    }});
}}

setInterval(checkReminders, 30000);
</script>"""
    return page("Reminders", body, "reminders", get_patient())


# =========================================================
# ACTIVITIES / GAMES / GK
# =========================================================

@app.route("/activities")
def activities():
    if not require_login(): return redirect("/login")
    body = """
    <h1 class="page-title">Cognitive Activities</h1><p class="page-sub">Short, friendly activities for memory, attention and general knowledge.</p>
    <div class="game"><div class="eyebrow">MEMORY GAME</div><h2>Remember the sequence</h2>
    <p>Watch the four symbols for a few seconds, then choose them in the same order.</p>
    <div id="seq" style="font-size:45px;text-align:center;min-height:70px">🍎 🏠 🎵 🌳</div>
    <button class="btn" onclick="startSequence()">Start Memory Game</button>
    <div id="seqButtons" class="game-options" style="margin-top:15px;display:none">
      <button onclick="seqAnswer('🍎')">🍎</button><button onclick="seqAnswer('🏠')">🏠</button>
      <button onclick="seqAnswer('🎵')">🎵</button><button onclick="seqAnswer('🌳')">🌳</button>
    </div><div id="seqResult" class="result"></div></div>

    <div class="game"><div class="eyebrow">GENERAL KNOWLEDGE</div><h2>Identify the answer</h2>
    <p id="gkQuestion">Which planet is known as the Red Planet?</p>
    <div class="game-options">
      <button onclick="gk('Earth')">Earth</button><button onclick="gk('Mars')">Mars</button><button onclick="gk('Venus')">Venus</button>
    </div><div id="gkResult" class="result"></div></div>

    <div class="game"><div class="eyebrow">ATTENTION</div><h2>Odd one out</h2>
    <p>Which one is different?</p><div class="game-options">
      <button onclick="odd('Apple')">🍎 Apple</button><button onclick="odd('Banana')">🍌 Banana</button><button onclick="odd('Car')">🚗 Car</button>
    </div><div id="oddResult" class="result"></div></div>

    <div class="game">
    <div class="eyebrow">TASK ANIMATION</div>
    <h2>How to drink water</h2>

    <div id="taskStep" style="text-align:center;font-size:70px;animation:breathe 3s infinite">
        🥤
    </div>

    <h3 id="taskText" class="center">Step 1: Pick up the glass</h3>

    <div class="center" style="margin-top:15px">
        <button class="btn" onclick="nextTaskStep()">Next Step →</button>
    </div>

    <div id="taskResult" class="result"></div>
</div>
    <script>
    let sequence = ['🍎','🏠','🎵','🌳'];
let user = [];

function startSequence(){{
    user = [];

    document.getElementById('seq').innerText = sequence.join(' ');
    document.getElementById('seqButtons').style.display = 'none';
    document.getElementById('seqResult').innerText = 'Remember the sequence...';

    setTimeout(function(){{
        document.getElementById('seq').innerText = 'Your turn!';
        document.getElementById('seqButtons').style.display = 'grid';
        document.getElementById('seqResult').innerText =
            'Select the symbols in the same order.';
    }}, 2500);
}}

 function seqAnswer(x){{
    if(user.length >= sequence.length) return;

    user.push(x);

    const buttons = document.querySelectorAll('#seqButtons button');

buttons.forEach(btn => {{
    if(btn.innerText.includes(x)) {{
        btn.classList.add('selected');
        btn.innerHTML = '✓ ' + x + ' <small>Selected</small>';
    }}
}});


    document.getElementById('seqResult').innerText =
        'Selected ' + user.length + ' of ' + sequence.length;

    if(user.length === sequence.length){{
        let correct = true;

        for(let i = 0; i < sequence.length; i++){{
            if(user[i] !== sequence[i]){{
                correct = false;
                break;
            }}
        }}

        if(correct){{
            document.getElementById('seqResult').innerText =
                '✓ Excellent memory!';

            const message = new SpeechSynthesisUtterance(
                'Excellent! Activity completed. Well done!'
            );

            window.speechSynthesis.speak(message);
        }} else {{
            document.getElementById('seqResult').innerText =
                'Try again — you can do it.';
        }}
    }}
}}

let taskStep = 1;

function nextTaskStep(){{
    taskStep++;

    if(taskStep === 2){{
        document.getElementById('taskStep').innerText = '💧';
        document.getElementById('taskText').innerText =
            'Step 2: Take a comfortable sip';
    }}
    else if(taskStep === 3){{
        document.getElementById('taskStep').innerText = '🥤';
        document.getElementById('taskText').innerText =
            'Step 3: Put the glass down';
    }}
    else if(taskStep === 4){{
        document.getElementById('taskStep').innerText = '✅';
        document.getElementById('taskText').innerText =
            'Step 4: Task completed!';
        document.getElementById('taskResult').innerText =
            '✓ Well done! You completed the activity.';

        const message = new SpeechSynthesisUtterance(
            'Well done! You completed the activity.'
        );
        window.speechSynthesis.speak(message);
    }}
}}

function gk(x){{
    document.getElementById('gkResult').innerText =
        x === 'Mars'
        ? '✓ Correct! Mars is the Red Planet.'
        : 'Try again.';
}}

function odd(x){{
    document.getElementById('oddResult').innerText =
        x === 'Car'
        ? '✓ Correct! Car is different.'
        : 'Try again.';
}}
    </script>
    """
    return page("Activities", body, "activities", get_patient())


# =========================================================
# EXERCISE + YOGA BREATHING
# =========================================================

@app.route("/exercise")
def exercise():
    if not require_login(): return redirect("/login")
    body = """
    <h1 class="page-title">Exercise & Yoga</h1><p class="page-sub">Gentle movement ideas with a simple breathing animation.</p>
    <div class="grid">
      <div class="panel col-6 center"><div class="eyebrow">BREATHING</div><h2>Calm breathing</h2>
      <div class="exercise-animation">🌿</div><h3 id="breathText">Breathe in</h3>
      <p>Follow the circle slowly. Stop if you feel uncomfortable.</p>
      <button class="btn" onclick="startBreath()">Start / Pause</button></div>
      <div class="panel col-6"><div class="eyebrow">GENTLE ACTIVITY</div><h2>Movement routine</h2>
      <div class="status-row"><span>🧘 Shoulder rolls</span><span>1 min</span></div>
      <div class="status-row"><span>🚶 Slow walk</span><span>5 min</span></div>
      <div class="status-row"><span>🙆 Gentle stretch</span><span>2 min</span></div>
      <div class="status-row"><span>🪑 Seated movement</span><span>3 min</span></div>
      <div class="notice">For an elderly user, keep movement gentle and stop if there is pain, dizziness or discomfort.</div></div>
    </div>
    <script>
    let breathTimer=null,phase=0;
    function startBreath(){{
    if(breathTimer){{
        clearInterval(breathTimer);
        breathTimer=null;
        window.speechSynthesis.cancel();
        return;
    }}

    const phases = [
        'Breathe in slowly',
        'Hold gently',
        'Breathe out slowly',
        'Rest'
    ];

    phase = 0;

    document.getElementById('breathText').innerText = phases[phase];

    let message = new SpeechSynthesisUtterance(phases[phase]);
    message.rate = 0.8;
    window.speechSynthesis.speak(message);

    breathTimer = setInterval(()=>{{
        phase = (phase + 1) % 4;

        document.getElementById('breathText').innerText =
            phases[phase];

        window.speechSynthesis.cancel();

        let voice = new SpeechSynthesisUtterance(phases[phase]);
        voice.rate = 0.8;
        window.speechSynthesis.speak(voice);

    }}, 3000);
}}
    </script>
    """
    return page("Exercise & Yoga", body, "exercise", get_patient())


# =========================================================
# DEEP SLEEP METER
# =========================================================

@app.route("/sleep")
def sleep():
    if not require_login(): return redirect("/login")
    body = """
    <h1 class="page-title">Deep Sleep Meter</h1><p class="page-sub">A simple prototype sleep-quality view with a calming mode.</p>
    <div class="grid">
      <div class="panel col-6 center"><div class="eyebrow">SLEEP SCORE</div>
      <div class="sleep-ring" id="ring"><div class="sleep-inner"><div><div class="big-number" id="sleepScore">78%</div><div class="small">restful</div></div></div></div>
      <input id="sleepRange" type="range" min="0" max="100" value="78" style="width:80%" oninput="setSleep(this.value)">
      <p class="small">Demo meter — not a medical sleep measurement.</p></div>
      <div class="panel col-6"><div class="eyebrow">WIND DOWN</div><h2>Calm mode</h2>
      <p>Dim the interface and play a soft generated tone using the browser.</p>
      <button class="btn btn-mint" onclick="calm()">🌙 Start calm mode</button>
      <div id="calmMsg" class="notice">Ready for a quiet moment.</div></div>
    </div>
    <script>
    function setSleep(v){{document.getElementById('sleepScore').innerText=v+'%';document.getElementById('ring').style.background='conic-gradient(#4943a5 0 '+v+'%,#e9e5dc '+v+'% 100%)'}}
    let audioCtx;
    function calm(){{try{{audioCtx=audioCtx||new(window.AudioContext||window.webkitAudioContext)();let o=audioCtx.createOscillator(),g=audioCtx.createGain();o.frequency.value=220;g.gain.value=.025;o.connect(g);g.connect(audioCtx.destination);o.start();setTimeout(()=>o.stop(),4000);document.getElementById('calmMsg').innerText='🌙 Calm tone playing for a few seconds.'}}catch(e){{document.getElementById('calmMsg').innerText='Calm mode is unavailable in this browser.'}}}}
    </script>
    """
    return page("Deep Sleep", body, "sleep", get_patient())


# =========================================================
# LOCATION FINDER / ALARM
# =========================================================

@app.route("/location")
def location():
    if not require_login(): return redirect("/login")
    body = """
    <h1 class="page-title">Location Finder</h1><p class="page-sub">Use the browser's location permission to find the current position and set a local alarm.</p>
    <div class="grid">
      <div class="panel col-7"><div class="eyebrow">CURRENT LOCATION</div><h2>Where am I?</h2>
      <div id="loc" class="location-box">Location not requested yet.</div>
      <button class="btn" style="margin-top:15px" onclick="findLocation()">📍 Find my location</button>
      <p class="small">Your browser will ask for location permission. This prototype displays coordinates only.</p></div>
      <div class="panel col-5"><div class="eyebrow">ALARM</div><h2>Set an alarm</h2>
      <input id="alarmTime" type="time" style="width:100%;padding:13px;border:1px solid #ddd;border-radius:12px">
      <button class="btn btn-gold" style="width:100%;margin-top:15px" onclick="setAlarm()">⏰ Set alarm</button>
      <div id="alarmMsg" class="notice">No alarm set.</div></div>
    </div>
    <script>
    function findLocation(){{let box=document.getElementById('loc');if(!navigator.geolocation){{box.innerText='Geolocation is not supported.';return;}}
    box.innerText='Finding location...';navigator.geolocation.getCurrentPosition(p=>{{box.innerHTML='<b>Latitude:</b> '+p.coords.latitude.toFixed(5)+'<br><b>Longitude:</b> '+p.coords.longitude.toFixed(5);}},()=>box.innerText='Location permission was denied or unavailable.')}}
    let alarm=null;
    function setAlarm(){{let t=document.getElementById('alarmTime').value;if(!t){{alert('Choose a time first.');return;}}clearInterval(alarm);alarm=setInterval(()=>{{let n=new Date(),now=n.toTimeString().slice(0,5);if(now===t){{alert('🔔 MEMORA alarm: '+t);clearInterval(alarm);}}}},1000);document.getElementById('alarmMsg').innerText='Alarm set for '+t+'. Keep this page open for the demo.'}}
    </script>
    """
    return page("Location Finder", body, "location", get_patient())


# =========================================================
# CAREGIVER DASHBOARD / PROGRESS
# =========================================================

@app.route("/caregiver")
def caregiver():
    if not require_login(): return redirect("/login")
    conn = db()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY task_time").fetchall()
    reminders = conn.execute("SELECT * FROM reminders ORDER BY reminder_time").fetchall()
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE done=1").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    p = get_patient()
    pct = int(done/total*100) if total else 0
    task_rows = "".join(f"<div class='status-row'><span>{t['title']}</span><b>{'✓ Complete' if t['done'] else 'Pending'}</b></div>" for t in tasks)
    rem_rows = "".join(f"<div class='status-row'><span>{r['title']}</span><b>{'✓ Done' if r['done'] else 'Active'}</b></div>" for r in reminders)
    body = f"""
    <h1 class="page-title">Caregiver Dashboard</h1><p class="page-sub">A quick view of patient information, tasks, reminders and progress.</p>
    <div class="grid">
      <div class="panel col-5"><div class="eyebrow">PATIENT</div><h2>{p['name']}</h2>
      <div class="status-row"><span>Age</span><b>{p['age']}</b></div><div class="status-row"><span>Gender</span><b>{p['gender']}</b></div>
      <div class="status-row"><span>Phone</span><b>{p['phone']}</b></div><div class="status-row"><span>Caregiver</span><b>{p['caregiver']}</b></div></div>
      <div class="panel col-7"><div class="eyebrow">TODAY'S PROGRESS</div><h2>{pct}% complete</h2><div class="meter"><div class="meter-fill" style="width:{pct}%"></div></div>
      <p class="small">{done} of {total} routine tasks completed.</p></div>
      <div class="panel col-6"><div class="eyebrow">ACTIVITIES</div><h2>Daily status</h2>{task_rows}</div>
      <div class="panel col-6"><div class="eyebrow">REMINDERS</div><h2>Reminder status</h2>{rem_rows}</div>
    </div>"""
    return page("Caregiver", body, "caregiver", p)


@app.route("/progress")
def progress():
    return redirect("/caregiver")


# =========================================================
# SETTINGS / LOGOUT
# =========================================================

@app.route("/settings")
def settings():
    if not require_login(): return redirect("/login")
    body = """
    <h1 class="page-title">Settings</h1><p class="page-sub">Prototype controls and privacy information.</p>
    <div class="grid"><div class="panel col-6"><h2>Privacy</h2>
    <div class="status-row"><span>Personal memories</span><b>🔐 PIN protected</b></div>
    <div class="status-row"><span>Demo PIN</span><b>1234</b></div>
    <div class="notice">This is a hackathon prototype. The PIN is demonstration-level protection, not production authentication.</div></div>
    <div class="panel col-6"><h2>About MEMORA</h2>
    <p>MEMORA is an AI-based cognitive and daily-life assistance platform concept for elderly users and caregivers.</p>
    <p>It brings memories, voice interaction, cognitive activities, routines, reminders, gentle exercise, sleep support and caregiver monitoring into one simple interface.</p>
    <a class="btn" href="/logout">Log out</a></div></div>
    """
    return page("Settings", body, "today", get_patient())


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================================================
# START
# =========================================================

init_database()

if __name__ == "__main__":
    app.run(debug=True)
