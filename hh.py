# =============================================================================
#  Hospital Appointment Scheduling System
#  Tech Stack: Python Flask + MySQL + HTML/CSS (all-in-one file)
#  Run: pip install flask mysql-connector-python
#       python app.py
# =============================================================================

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import mysql.connector
import hashlib
import os

# ─── App Configuration ───────────────────────────────────────────────────────

app = Flask(__name__)
# Secret key for session encryption — change this in production!
app.secret_key = "hospital_secret_key_change_in_prod"

# ─── Database Configuration ──────────────────────────────────────────────────
# Update these values to match your MySQL setup

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",          # your MySQL username
    "password": "Harshit@12", # your MySQL password
    "database": "hospital_db"
}


def get_db():
    """Return a fresh MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """
    Create the database and tables if they don't exist.
    Called once when the app starts.
    """
    # First connect without specifying a database to create it if needed
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()

    # Create the database
    cursor.execute("CREATE DATABASE IF NOT EXISTS hospital_db")
    cursor.execute("USE hospital_db")

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)

    # Create appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            patient    VARCHAR(150) NOT NULL,
            doctor     VARCHAR(150) NOT NULL,
            department VARCHAR(100) NOT NULL,
            date       DATE         NOT NULL,
            status     VARCHAR(50)  DEFAULT 'Pending'
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅  Database and tables ready.")


def hash_password(password):
    """SHA-256 hash a password (add salt for production use)."""
    return hashlib.sha256(password.encode()).hexdigest()


# ─── HTML Templates ──────────────────────────────────────────────────────────

# Shared base styles injected into every page
BASE_STYLE = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  /* ── Reset & Base ── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --navy:      #0d1f3c;
    --teal:      #0f7b82;
    --teal-light:#12979f;
    --cream:     #f5f0e8;
    --white:     #ffffff;
    --border:    #dde4ed;
    --text:      #1a2940;
    --muted:     #6b7e99;
    --danger:    #c0392b;
    --success:   #1a7a4a;
    --radius:    10px;
    --shadow:    0 4px 24px rgba(13,31,60,.10);
    --shadow-lg: 0 12px 48px rgba(13,31,60,.16);
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--cream);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── Navigation ── */
  nav {
    background: var(--navy);
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 12px rgba(0,0,0,.25);
  }

  .nav-brand {
    display: flex;
    align-items: center;
    gap: .6rem;
    text-decoration: none;
    color: var(--white);
  }

  .nav-brand .logo-icon {
    width: 32px; height: 32px;
    background: var(--teal);
    border-radius: 8px;
    display: grid; place-items: center;
    font-size: 1.1rem;
  }

  .nav-brand span {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    letter-spacing: .02em;
  }

  .nav-links {
    display: flex;
    gap: .25rem;
    list-style: none;
  }

  .nav-links a {
    color: rgba(255,255,255,.75);
    text-decoration: none;
    font-size: .88rem;
    font-weight: 500;
    padding: .45rem .85rem;
    border-radius: 6px;
    transition: all .2s;
    letter-spacing: .02em;
  }

  .nav-links a:hover, .nav-links a.active {
    color: var(--white);
    background: rgba(255,255,255,.12);
  }

  .nav-links a.logout {
    color: #f08080;
  }
  .nav-links a.logout:hover {
    background: rgba(192,57,43,.25);
    color: #ffb3b3;
  }

  /* ── Page Wrapper ── */
  .page {
    max-width: 960px;
    margin: 3rem auto;
    padding: 0 1.5rem;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: var(--navy);
    margin-bottom: .35rem;
  }

  .page-header p {
    color: var(--muted);
    font-size: .95rem;
  }

  /* ── Card ── */
  .card {
    background: var(--white);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 2rem;
    border: 1px solid var(--border);
  }

  /* ── Form Elements ── */
  .form-group {
    margin-bottom: 1.25rem;
  }

  label {
    display: block;
    font-size: .84rem;
    font-weight: 600;
    color: var(--navy);
    margin-bottom: .45rem;
    letter-spacing: .03em;
    text-transform: uppercase;
  }

  input, select {
    width: 100%;
    padding: .7rem 1rem;
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: .95rem;
    color: var(--text);
    background: #fafbfd;
    transition: border-color .2s, box-shadow .2s;
    outline: none;
  }

  input:focus, select:focus {
    border-color: var(--teal);
    box-shadow: 0 0 0 3px rgba(15,123,130,.12);
    background: var(--white);
  }

  /* ── Buttons ── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: .5rem;
    padding: .72rem 1.6rem;
    border: none;
    border-radius: var(--radius);
    font-family: 'DM Sans', sans-serif;
    font-size: .95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all .2s;
    text-decoration: none;
    letter-spacing: .02em;
  }

  .btn-primary {
    background: var(--teal);
    color: var(--white);
    width: 100%;
    justify-content: center;
    margin-top: .5rem;
  }

  .btn-primary:hover {
    background: var(--teal-light);
    box-shadow: 0 4px 16px rgba(15,123,130,.35);
    transform: translateY(-1px);
  }

  .btn-sm {
    padding: .35rem .9rem;
    font-size: .8rem;
    border-radius: 6px;
  }

  /* ── Alerts ── */
  .alert {
    padding: .85rem 1rem;
    border-radius: var(--radius);
    font-size: .9rem;
    font-weight: 500;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    gap: .6rem;
  }

  .alert-error {
    background: #fdf0ef;
    border: 1px solid #f5c6c2;
    color: var(--danger);
  }

  .alert-success {
    background: #edf7f1;
    border: 1px solid #b7e4ca;
    color: var(--success);
  }

  /* ── Table ── */
  .table-wrap {
    overflow-x: auto;
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: .9rem;
  }

  thead {
    background: var(--navy);
    color: var(--white);
  }

  thead th {
    padding: .85rem 1rem;
    text-align: left;
    font-weight: 600;
    font-size: .8rem;
    letter-spacing: .05em;
    text-transform: uppercase;
  }

  tbody tr {
    border-bottom: 1px solid var(--border);
    transition: background .15s;
  }

  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: #f7f9fc; }

  tbody td {
    padding: .9rem 1rem;
    color: var(--text);
  }

  .badge {
    display: inline-block;
    padding: .25rem .7rem;
    border-radius: 20px;
    font-size: .75rem;
    font-weight: 600;
    letter-spacing: .03em;
  }

  .badge-pending  { background: #fff3cd; color: #856404; }
  .badge-confirmed{ background: #d1e7dd; color: #0f5132; }
  .badge-cancelled{ background: #f8d7da; color: #842029; }

  /* ── Stats row (home page) ── */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px,1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    box-shadow: var(--shadow);
  }

  .stat-card .number {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: var(--teal);
    line-height: 1;
  }

  .stat-card .label {
    font-size: .82rem;
    color: var(--muted);
    margin-top: .3rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .04em;
  }

  /* ── Login page ── */
  .login-wrap {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0d1f3c 0%, #0f7b82 100%);
    padding: 2rem;
  }

  .login-box {
    background: var(--white);
    border-radius: 16px;
    padding: 2.8rem 2.5rem;
    width: 100%;
    max-width: 420px;
    box-shadow: var(--shadow-lg);
  }

  .login-logo {
    text-align: center;
    margin-bottom: 2rem;
  }

  .login-logo .icon {
    width: 56px; height: 56px;
    background: var(--teal);
    border-radius: 14px;
    display: inline-grid;
    place-items: center;
    font-size: 1.6rem;
    margin-bottom: .75rem;
  }

  .login-logo h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: var(--navy);
  }

  .login-logo p {
    color: var(--muted);
    font-size: .88rem;
    margin-top: .3rem;
  }

  .divider {
    text-align: center;
    margin: 1.5rem 0 1rem;
    font-size: .78rem;
    color: var(--muted);
    letter-spacing: .08em;
    text-transform: uppercase;
  }

  .register-link {
    text-align: center;
    font-size: .88rem;
    color: var(--muted);
    margin-top: 1.2rem;
  }

  .register-link a {
    color: var(--teal);
    font-weight: 600;
    text-decoration: none;
  }

  /* ── Two-column form ── */
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  @media (max-width: 600px) {
    .form-row { grid-template-columns: 1fr; }
    .nav-links a span { display: none; }
  }

  /* ── Empty state ── */
  .empty {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--muted);
  }

  .empty .icon { font-size: 2.5rem; margin-bottom: .75rem; }
  .empty p { font-size: .95rem; }
</style>
"""

# Shared navigation bar (shown only when logged in)
NAV = """
<nav>
  <a href="/home" class="nav-brand">
    <span class="logo-icon">🏥</span>
    <span>MediSchedule</span>
  </a>
  <ul class="nav-links">
    <li><a href="/home"              id="nav-home">Home</a></li>
    <li><a href="/book"              id="nav-book">Book Appointment</a></li>
    <li><a href="/appointments"      id="nav-view">View Appointments</a></li>
    <li><a href="/logout" class="logout">Logout</a></li>
  </ul>
</nav>
<script>
  // Highlight active nav link
  const path = window.location.pathname;
  if (path === '/home')         document.getElementById('nav-home').classList.add('active');
  if (path === '/book')         document.getElementById('nav-book').classList.add('active');
  if (path === '/appointments') document.getElementById('nav-view').classList.add('active');
</script>
"""


# ─── LOGIN PAGE ──────────────────────────────────────────────────────────────

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Login – MediSchedule</title>
  """ + BASE_STYLE + """
</head>
<body>
<div class="login-wrap">
  <div class="login-box">

    <div class="login-logo">
      <div class="icon">🏥</div>
      <h1>MediSchedule</h1>
      <p>Hospital Appointment System</p>
    </div>

    {% if error %}
    <div class="alert alert-error">⚠ {{ error }}</div>
    {% endif %}

    <form method="POST" action="/login">
      <div class="form-group">
        <label>Username</label>
        <input type="text" name="username" placeholder="Enter your username"
               required autocomplete="username">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" placeholder="Enter your password"
               required autocomplete="current-password">
      </div>
      <button type="submit" class="btn btn-primary">Sign In →</button>
    </form>

    <div class="divider">or</div>
    <div class="register-link">
      Don't have an account? <a href="/register">Register here</a>
    </div>

  </div>
</div>
</body>
</html>
"""


# ─── REGISTER PAGE ───────────────────────────────────────────────────────────

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Register – MediSchedule</title>
  """ + BASE_STYLE + """
</head>
<body>
<div class="login-wrap">
  <div class="login-box">

    <div class="login-logo">
      <div class="icon">🏥</div>
      <h1>Create Account</h1>
      <p>Join MediSchedule today</p>
    </div>

    {% if error %}
    <div class="alert alert-error">⚠ {{ error }}</div>
    {% endif %}

    {% if success %}
    <div class="alert alert-success">✓ {{ success }}</div>
    {% endif %}

    <form method="POST" action="/register">
      <div class="form-group">
        <label>Username</label>
        <input type="text" name="username" placeholder="Choose a username" required minlength="3">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" placeholder="Choose a password" required minlength="6">
      </div>
      <div class="form-group">
        <label>Confirm Password</label>
        <input type="password" name="confirm" placeholder="Repeat your password" required minlength="6">
      </div>
      <button type="submit" class="btn btn-primary">Create Account →</button>
    </form>

    <div class="register-link" style="margin-top:1.2rem">
      Already have an account? <a href="/">Login</a>
    </div>

  </div>
</div>
</body>
</html>
"""


# ─── HOME PAGE ───────────────────────────────────────────────────────────────

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Home – MediSchedule</title>
  """ + BASE_STYLE + """
</head>
<body>
""" + NAV + """
<div class="page">

  <div class="page-header">
    <h1>Welcome back, {{ username }} 👋</h1>
    <p>Here's a quick overview of the appointment system.</p>
  </div>

  <!-- Statistics -->
  <div class="stats">
    <div class="stat-card">
      <div class="number">{{ total }}</div>
      <div class="label">Total Appointments</div>
    </div>
    <div class="stat-card">
      <div class="number">{{ pending }}</div>
      <div class="label">Pending</div>
    </div>
    <div class="stat-card">
      <div class="number">{{ confirmed }}</div>
      <div class="label">Confirmed</div>
    </div>
    <div class="stat-card">
      <div class="number">{{ cancelled }}</div>
      <div class="label">Cancelled</div>
    </div>
  </div>

  <!-- Quick actions -->
  <div class="card">
    <h2 style="font-family:'DM Serif Display',serif;font-size:1.3rem;margin-bottom:1rem;color:var(--navy)">
      Quick Actions
    </h2>
    <div style="display:flex;gap:1rem;flex-wrap:wrap">
      <a href="/book" class="btn btn-primary" style="width:auto">
        📅 Book New Appointment
      </a>
      <a href="/appointments" class="btn btn-primary"
         style="width:auto;background:var(--navy)">
        📋 View All Appointments
      </a>
    </div>
  </div>

  <!-- Recent appointments (last 5) -->
  {% if recent %}
  <div style="margin-top:2rem">
    <div class="page-header">
      <h1 style="font-size:1.4rem">Recent Appointments</h1>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th><th>Patient</th><th>Doctor</th>
            <th>Department</th><th>Date</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          {% for row in recent %}
          <tr>
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
            <td>Dr. {{ row[2] }}</td>
            <td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td>
            <td>
              <span class="badge badge-{{ row[5]|lower }}">{{ row[5] }}</span>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
  {% endif %}

</div>
</body>
</html>
"""


# ─── BOOK APPOINTMENT PAGE ───────────────────────────────────────────────────

BOOK_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Book Appointment – MediSchedule</title>
  """ + BASE_STYLE + """
</head>
<body>
""" + NAV + """
<div class="page">

  <div class="page-header">
    <h1>Book an Appointment</h1>
    <p>Fill in the details below to schedule your visit.</p>
  </div>

  {% if error %}
  <div class="alert alert-error">⚠ {{ error }}</div>
  {% endif %}

  {% if success %}
  <div class="alert alert-success">✓ {{ success }}</div>
  {% endif %}

  <div class="card">
    <form method="POST" action="/book">

      <div class="form-row">
        <div class="form-group">
          <label>Patient Full Name</label>
          <input type="text" name="patient" placeholder="e.g. Ravi Kumar"
                 required minlength="2" maxlength="150">
        </div>
        <div class="form-group">
          <label>Doctor Name</label>
          <input type="text" name="doctor" placeholder="e.g. Sharma"
                 required minlength="2" maxlength="150">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Department</label>
          <select name="department" required>
            <option value="" disabled selected>Select department…</option>
            <option>Cardiology</option>
            <option>Neurology</option>
            <option>Orthopedics</option>
            <option>Dermatology</option>
            <option>Pediatrics</option>
            <option>Gynecology</option>
            <option>ENT</option>
            <option>Ophthalmology</option>
            <option>Psychiatry</option>
            <option>General Medicine</option>
            <option>Oncology</option>
            <option>Radiology</option>
          </select>
        </div>
        <div class="form-group">
          <label>Appointment Date</label>
          <input type="date" name="date" required id="appt-date">
        </div>
      </div>

      <button type="submit" class="btn btn-primary">Confirm Appointment →</button>
    </form>
  </div>

</div>

<script>
  // Prevent selecting past dates
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('appt-date').setAttribute('min', today);
</script>
</body>
</html>
"""


# ─── VIEW APPOINTMENTS PAGE ──────────────────────────────────────────────────

VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Appointments – MediSchedule</title>
  """ + BASE_STYLE + """
  <style>
    .filters {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      align-items: flex-end;
      margin-bottom: 1.5rem;
    }
    .filters .form-group { margin-bottom: 0; flex: 1; min-width: 160px; }
    .filters .btn { padding: .68rem 1.2rem; margin-top: 0; width: auto; }
  </style>
</head>
<body>
""" + NAV + """
<div class="page">

  <div class="page-header">
    <h1>All Appointments</h1>
    <p>Browse, search, and manage every appointment in the system.</p>
  </div>

  <!-- Filter / Search form -->
  <form method="GET" action="/appointments">
    <div class="filters">
      <div class="form-group">
        <label>Search Patient</label>
        <input type="text" name="search" placeholder="Patient name…"
               value="{{ search }}">
      </div>
      <div class="form-group">
        <label>Filter by Status</label>
        <select name="status">
          <option value="">All Statuses</option>
          <option {% if status_filter == 'Pending'   %}selected{% endif %}>Pending</option>
          <option {% if status_filter == 'Confirmed' %}selected{% endif %}>Confirmed</option>
          <option {% if status_filter == 'Cancelled' %}selected{% endif %}>Cancelled</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary" style="width:auto">Search</button>
      <a href="/appointments" class="btn" style="background:#eee;color:var(--navy)">Reset</a>
    </div>
  </form>

  {% if appointments %}
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Patient</th>
          <th>Doctor</th>
          <th>Department</th>
          <th>Date</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for row in appointments %}
        <tr>
          <td style="color:var(--muted);font-size:.8rem">{{ row[0] }}</td>
          <td><strong>{{ row[1] }}</strong></td>
          <td>Dr. {{ row[2] }}</td>
          <td>{{ row[3] }}</td>
          <td>{{ row[4] }}</td>
          <td>
            <span class="badge badge-{{ row[5]|lower }}">{{ row[5] }}</span>
          </td>
          <td style="display:flex;gap:.4rem;flex-wrap:wrap">
            <!-- Confirm button -->
            <form method="POST" action="/update_status">
              <input type="hidden" name="id"     value="{{ row[0] }}">
              <input type="hidden" name="status" value="Confirmed">
              <button type="submit" class="btn btn-sm"
                      style="background:#d1e7dd;color:#0f5132;border:none;cursor:pointer">
                ✓ Confirm
              </button>
            </form>
            <!-- Cancel button -->
            <form method="POST" action="/update_status">
              <input type="hidden" name="id"     value="{{ row[0] }}">
              <input type="hidden" name="status" value="Cancelled">
              <button type="submit" class="btn btn-sm"
                      style="background:#f8d7da;color:#842029;border:none;cursor:pointer">
                ✕ Cancel
              </button>
            </form>
            <!-- Delete button -->
            <form method="POST" action="/delete_appointment"
                  onsubmit="return confirm('Delete this appointment?')">
              <input type="hidden" name="id" value="{{ row[0] }}">
              <button type="submit" class="btn btn-sm"
                      style="background:#e9ecef;color:#495057;border:none;cursor:pointer">
                🗑 Delete
              </button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <p style="margin-top:1rem;font-size:.85rem;color:var(--muted)">
    Showing {{ appointments|length }} record(s).
  </p>

  {% else %}
  <div class="card">
    <div class="empty">
      <div class="icon">📋</div>
      <p>No appointments found{% if search or status_filter %} matching your filters{% endif %}.</p>
    </div>
  </div>
  {% endif %}

</div>
</body>
</html>
"""


# ─── Flask Routes ─────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator: redirect to login if user is not in session."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Login ──────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    # Already logged in → go straight home
    if "username" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Basic validation
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE,
                                          error="Please fill in all fields.")

        # Check credentials in DB
        conn   = get_db()
        cursor = conn.cursor()
        # Parameterized query — prevents SQL injection
        cursor.execute(
            "SELECT id FROM users WHERE username = %s AND password = %s",
            (username, hash_password(password))
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["username"] = username   # Store in session
            return redirect(url_for("home"))
        else:
            return render_template_string(LOGIN_TEMPLATE,
                                          error="Invalid username or password.")

    return render_template_string(LOGIN_TEMPLATE, error=None)


# ── Register ──────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        # Validation
        if not username or not password or not confirm:
            return render_template_string(REGISTER_TEMPLATE,
                                          error="All fields are required.", success=None)
        if len(username) < 3:
            return render_template_string(REGISTER_TEMPLATE,
                                          error="Username must be at least 3 characters.", success=None)
        if len(password) < 6:
            return render_template_string(REGISTER_TEMPLATE,
                                          error="Password must be at least 6 characters.", success=None)
        if password != confirm:
            return render_template_string(REGISTER_TEMPLATE,
                                          error="Passwords do not match.", success=None)

        # Insert into DB (UNIQUE constraint handles duplicates)
        try:
            conn   = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hash_password(password))
            )
            conn.commit()
            cursor.close()
            conn.close()
            return render_template_string(REGISTER_TEMPLATE,
                                          error=None,
                                          success="Account created! You can now log in.")
        except mysql.connector.IntegrityError:
            return render_template_string(REGISTER_TEMPLATE,
                                          error="Username already taken. Choose another.", success=None)

    return render_template_string(REGISTER_TEMPLATE, error=None, success=None)


# ── Logout ────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()              # Remove all session data
    return redirect(url_for("login"))


# ── Home ──────────────────────────────────────────────────────────────────

@app.route("/home")
@login_required
def home():
    conn   = get_db()
    cursor = conn.cursor()

    # Aggregate counts for dashboard stats
    cursor.execute("SELECT COUNT(*) FROM appointments")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Confirmed'")
    confirmed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Cancelled'")
    cancelled = cursor.fetchone()[0]

    # Last 5 appointments for the "recent" section
    cursor.execute("""
        SELECT id, patient, doctor, department, date, status
        FROM appointments
        ORDER BY id DESC LIMIT 5
    """)
    recent = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template_string(HOME_TEMPLATE,
                                  username=session["username"],
                                  total=total,
                                  pending=pending,
                                  confirmed=confirmed,
                                  cancelled=cancelled,
                                  recent=recent)


# ── Book Appointment ──────────────────────────────────────────────────────

@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":
        patient    = request.form.get("patient",    "").strip()
        doctor     = request.form.get("doctor",     "").strip()
        department = request.form.get("department", "").strip()
        date       = request.form.get("date",       "").strip()

        # Form validation
        if not all([patient, doctor, department, date]):
            return render_template_string(BOOK_TEMPLATE,
                                          error="All fields are required.",
                                          success=None)

        # Insert with default status = 'Pending'
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (patient, doctor, department, date, status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (patient, doctor, department, date))
        conn.commit()
        cursor.close()
        conn.close()

        return render_template_string(BOOK_TEMPLATE,
                                      error=None,
                                      success=f"Appointment booked for {patient} on {date}!")

    return render_template_string(BOOK_TEMPLATE, error=None, success=None)


# ── View Appointments ─────────────────────────────────────────────────────

@app.route("/appointments", methods=["GET"])
@login_required
def appointments():
    search        = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    conn   = get_db()
    cursor = conn.cursor()

    # Build query dynamically based on filters
    query  = "SELECT id, patient, doctor, department, date, status FROM appointments WHERE 1=1"
    params = []

    if search:
        query  += " AND patient LIKE %s"
        params.append(f"%{search}%")

    if status_filter:
        query  += " AND status = %s"
        params.append(status_filter)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template_string(VIEW_TEMPLATE,
                                  appointments=rows,
                                  search=search,
                                  status_filter=status_filter)


# ── Update Appointment Status ─────────────────────────────────────────────

@app.route("/update_status", methods=["POST"])
@login_required
def update_status():
    appt_id    = request.form.get("id")
    new_status = request.form.get("status")

    # Only allow valid statuses to prevent tampering
    if new_status not in ("Confirmed", "Cancelled", "Pending"):
        return redirect(url_for("appointments"))

    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE appointments SET status = %s WHERE id = %s",
        (new_status, appt_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("appointments"))


# ── Delete Appointment ────────────────────────────────────────────────────

@app.route("/delete_appointment", methods=["POST"])
@login_required
def delete_appointment():
    appt_id = request.form.get("id")

    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = %s", (appt_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("appointments"))


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()                         # Create DB/tables on first run
    app.run(debug=True, port=5000)    