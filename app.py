# -*- coding: utf-8 -*-
import os
import sqlite3
import datetime
import random
import hashlib
import re
from flask import Flask, request, jsonify, render_template, session, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cleantex_final_secret_2026'
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
BUSINESS_ID = 1

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('database.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, currency TEXT, created_at TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, username TEXT UNIQUE, email TEXT,
            password_hash TEXT, role TEXT, full_name TEXT,
            phone TEXT, is_active INTEGER DEFAULT 1, created_at TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, user_id INTEGER, service_id INTEGER,
            item_description TEXT, date_taken TEXT, collection_date TEXT,
            subtotal REAL, tax_rate REAL, tax_amount REAL, total REAL,
            status TEXT, payment_status TEXT,
            client_name TEXT, client_phone TEXT, client_email TEXT,
            order_code TEXT UNIQUE, worker_id INTEGER, machine_id INTEGER)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, name TEXT, description TEXT,
            price REAL, is_active INTEGER DEFAULT 1)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, name TEXT, role TEXT,
            phone TEXT, wage REAL DEFAULT 0, hire_date TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, name TEXT, type TEXT, status TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS tax_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, tax_rate REAL, updated_at TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, order_id INTEGER, user_id INTEGER,
            complaint_text TEXT, reply TEXT, status TEXT, created_at TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER, setting_key TEXT, setting_value TEXT,
            updated_at TEXT, UNIQUE(business_id, setting_key))''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, token TEXT, expires_at TEXT)''')

        cur = conn.execute("SELECT COUNT(*) FROM businesses")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO businesses (name, currency, created_at) VALUES (?,?,?)",
                         ('Cleantex Main', 'KES', datetime.datetime.now().isoformat()))
            
            admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            conn.execute("INSERT INTO users (business_id, username, email, password_hash, role, full_name, is_active, created_at) VALUES (?,?,?,?,?,?,?,?)",
                         (BUSINESS_ID, 'admin', 'admin@cleantex.com', admin_hash, 'admin', 'System Admin', 1, datetime.datetime.now().isoformat()))
            
            services = [
                ('Coat & Jacket', 'Dry cleaning & pressing', 450.00),
                ('Wedding Dress', 'Specialist preservation', 1850.00),
                ('Suit & Tie', 'Full service', 750.00),
                ('Shirt (Standard)', 'Wash & iron', 250.00),
                ('Trousers', 'Dry clean & press', 350.00),
                ('Dress (Simple)', 'Hand wash & steam', 500.00),
                ('Curtains (per panel)', 'Deep clean', 900.00),
                ('Silk/Designer', 'Hand wash only', 1050.00),
                ('Leather Cleaning', 'Conditioning & cleaning', 1450.00)
            ]
            for name, desc, price in services:
                conn.execute("INSERT INTO services (business_id, name, description, price) VALUES (?,?,?,?)",
                             (BUSINESS_ID, name, desc, price))
            
            workers = [
                ('John Mwangi', 'Senior Cleaner', '0712345678', 800.00, '2024-01-15'),
                ('Sarah Kamau', 'Presser', '0723456789', 600.00, '2024-02-01'),
                ('Peter Omondi', 'Quality Control', '0734567890', 700.00, '2024-03-10')
            ]
            for name, role, phone, wage, hire in workers:
                conn.execute("INSERT INTO workers (business_id, name, role, phone, wage, hire_date) VALUES (?,?,?,?,?,?)",
                             (BUSINESS_ID, name, role, phone, wage, hire))
            
            machines = [
                ('Speed Queen Dry Cleaner', 'Dry Cleaning', 'Operational'),
                ('Electrolux Press', 'Pressing', 'Operational'),
                ('Bock Washing Machine', 'Washing', 'Maintenance')
            ]
            for name, typ, stat in machines:
                conn.execute("INSERT INTO machines (business_id, name, type, status) VALUES (?,?,?,?)",
                             (BUSINESS_ID, name, typ, stat))
            
            conn.execute("INSERT INTO tax_settings (business_id, tax_rate, updated_at) VALUES (?,?,?)",
                         (BUSINESS_ID, 8.0, datetime.datetime.now().isoformat()))
            
            # All settings keys including customer portal wallpapers
            settings_keys = [
                'hero_wallpaper', 'gallery_wallpaper', 'services_wallpaper',
                'coat_img', 'wedding_img', 'suit_img', 'leather_img',
                'card_wm_media_manager', 'card_wm_business_settings',
                'card_wm_new_order', 'card_wm_track_order', 'card_wm_all_users',
                'card_wm_financial', 'card_wm_workers_machines', 'card_wm_complaints',
                'card_wm_cust_new_order', 'card_wm_cust_pay_order',
                'card_wm_cust_my_orders', 'card_wm_cust_complaint'
            ]
            for key in settings_keys:
                conn.execute("INSERT INTO site_settings (business_id, setting_key, setting_value, updated_at) VALUES (?,?,?,?)",
                             (BUSINESS_ID, key, '', datetime.datetime.now().isoformat()))
            
            conn.commit()
            print("Database initialized successfully!")

init_db()

def get_setting(key):
    with get_db() as conn:
        row = conn.execute("SELECT setting_value FROM site_settings WHERE business_id=? AND setting_key=?", (BUSINESS_ID, key)).fetchone()
        return row['setting_value'] if row else ''

def delete_old_file(filepath):
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except:
            pass

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ---------- Authentication ----------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    phone_raw = data.get('phone', '').strip()
    phone = re.sub(r'[^0-9]', '', phone_raw)
    if not all([username, email, password, full_name, phone]):
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        return jsonify({'success': False, 'error': 'Username 3-30 alphanumeric or underscore'}), 400
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'success': False, 'error': 'Invalid email'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    if len(phone) < 10 or len(phone) > 13:
        return jsonify({'success': False, 'error': 'Phone must be 10-13 digits'}), 400
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email)).fetchone()
        if existing:
            return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
        conn.execute("INSERT INTO users (business_id, username, email, password_hash, role, full_name, phone, is_active, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                     (BUSINESS_ID, username, email, password_hash, 'customer', full_name, phone, 1, datetime.datetime.now().isoformat()))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1", (username, password_hash)).fetchone()
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
            return jsonify({'success': True, 'role': user['role'], 'username': user['username']})
    return jsonify({'success': False, 'error': 'Invalid credentials or account suspended'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth')
def check_auth():
    if 'user_id' in session:
        with get_db() as conn:
            user = conn.execute("SELECT role, username, is_active FROM users WHERE id=?", (session['user_id'],)).fetchone()
            if user and user['is_active'] == 1:
                return jsonify({'authenticated': True, 'role': user['role'], 'username': user['username']})
    return jsonify({'authenticated': False})

def admin_required():
    return 'user_id' in session and session.get('role') == 'admin'

@app.route('/api/admin/change-password', methods=['POST'])
def admin_change_password():
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    old = data.get('old_password')
    new = data.get('new_password')
    if not old or not new or len(new) < 6:
        return jsonify({'success': False, 'error': 'Invalid input'}), 400
    user_id = session['user_id']
    with get_db() as conn:
        user = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
        old_hash = hashlib.sha256(old.encode()).hexdigest()
        if user['password_hash'] != old_hash:
            return jsonify({'success': False, 'error': 'Old password incorrect'}), 401
        new_hash = hashlib.sha256(new.encode()).hexdigest()
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    suspend = data.get('suspend', True)
    with get_db() as conn:
        conn.execute("UPDATE users SET is_active=? WHERE id=?", (0 if suspend else 1, user_id))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    new_password = 'password123'
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    with get_db() as conn:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        conn.commit()
    return jsonify({'success': True, 'new_password': new_password})

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    with get_db() as conn:
        user = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        token = hashlib.sha256(f"{user['id']}{datetime.datetime.now().timestamp()}".encode()).hexdigest()[:32]
        expires = datetime.datetime.now() + datetime.timedelta(hours=1)
        conn.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?,?,?)",
                     (user['id'], token, expires.isoformat()))
        conn.commit()
        return jsonify({'success': True, 'token': token})

@app.route('/api/reset-password', methods=['POST'])
def reset_password_with_token():
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')
    if not token or not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Invalid input'}), 400
    with get_db() as conn:
        reset = conn.execute("SELECT user_id, expires_at FROM password_resets WHERE token=?", (token,)).fetchone()
        if not reset:
            return jsonify({'success': False, 'error': 'Invalid token'}), 400
        if datetime.datetime.now() > datetime.datetime.fromisoformat(reset['expires_at']):
            return jsonify({'success': False, 'error': 'Token expired'}), 400
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, reset['user_id']))
        conn.execute("DELETE FROM password_resets WHERE token=?", (token,))
        conn.commit()
    return jsonify({'success': True})

# ---------- Media Manager ----------
@app.route('/api/settings/<key>')
def get_setting_api(key):
    val = get_setting(key)
    return jsonify({'value': val})

@app.route('/api/upload-wallpaper', methods=['POST'])
def upload_wallpaper():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 401
    if 'image' not in request.files:
        return jsonify({'error': 'No file'}), 400
    section = request.form.get('section')
    # Allow all wallpaper keys including customer portal ones
    valid_sections = ['hero', 'gallery', 'services', 'cust_new_order', 'cust_pay_order', 'cust_my_orders', 'cust_complaint']
    if section not in valid_sections:
        return jsonify({'error': 'Invalid section'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    filename = secure_filename(f"{section}_wallpaper_{timestamp}.{ext}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    old_url = get_setting(f'{section}_wallpaper')
    if old_url:
        old_path = os.path.join('.', old_url.lstrip('/'))
        delete_old_file(old_path)
    file.save(filepath)
    print(f"Saved wallpaper: {filepath}")
    url = f'/static/uploads/{filename}'
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO site_settings (business_id, setting_key, setting_value, updated_at) VALUES (?,?,?,?)",
                     (BUSINESS_ID, f'{section}_wallpaper', url, datetime.datetime.now().isoformat()))
        conn.commit()
    return jsonify({'success': True, 'url': url})

GALLERY_TYPES = ['coat', 'wedding', 'suit', 'leather']

@app.route('/api/gallery-images', methods=['GET'])
def get_gallery_images():
    images = {}
    for img_type in GALLERY_TYPES:
        val = get_setting(f'{img_type}_img')
        images[f'{img_type}_img'] = val if val else ''
    return jsonify(images)

@app.route('/api/upload-gallery-image', methods=['POST'])
def upload_gallery_image():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 401
    if 'image' not in request.files:
        return jsonify({'error': 'No file'}), 400
    img_type = request.form.get('type')
    if img_type not in GALLERY_TYPES:
        return jsonify({'error': 'Invalid type'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    filename = secure_filename(f"{img_type}_img_{timestamp}.{ext}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    old_url = get_setting(f'{img_type}_img')
    if old_url:
        old_path = os.path.join('.', old_url.lstrip('/'))
        delete_old_file(old_path)
    file.save(filepath)
    print(f"Saved gallery: {filepath}")
    url = f'/static/uploads/{filename}'
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO site_settings (business_id, setting_key, setting_value, updated_at) VALUES (?,?,?,?)",
                     (BUSINESS_ID, f'{img_type}_img', url, datetime.datetime.now().isoformat()))
        conn.commit()
    return jsonify({'success': True, 'url': url})

# All card keys including customer portal
CARD_KEYS = [
    'media_manager', 'business_settings', 'new_order', 'track_order', 'all_users',
    'financial', 'workers_machines', 'complaints',
    'cust_new_order', 'cust_pay_order', 'cust_my_orders', 'cust_complaint'
]

@app.route('/api/card-watermarks', methods=['GET'])
def get_card_watermarks():
    watermarks = {}
    for key in CARD_KEYS:
        val = get_setting(f'card_wm_{key}')
        watermarks[key] = val if val else ''
    return jsonify(watermarks)

@app.route('/api/upload-card-watermark', methods=['POST'])
def upload_card_watermark():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 401
    if 'image' not in request.files:
        return jsonify({'error': 'No file'}), 400
    card_key = request.form.get('card_key')
    if card_key not in CARD_KEYS:
        return jsonify({'error': 'Invalid card key'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    filename = secure_filename(f"card_wm_{card_key}_{timestamp}.{ext}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    old_url = get_setting(f'card_wm_{card_key}')
    if old_url:
        old_path = os.path.join('.', old_url.lstrip('/'))
        delete_old_file(old_path)
    file.save(filepath)
    url = f'/static/uploads/{filename}'
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO site_settings (business_id, setting_key, setting_value, updated_at) VALUES (?,?,?,?)",
                     (BUSINESS_ID, f'card_wm_{card_key}', url, datetime.datetime.now().isoformat()))
        conn.commit()
    return jsonify({'success': True, 'url': url})

# ---------- Services ----------
@app.route('/api/services', methods=['GET'])
def get_services():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM services WHERE business_id=? AND is_active=1 ORDER BY id", (BUSINESS_ID,)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/services', methods=['POST'])
def add_service():
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price = float(data.get('price', 0))
    if not name or price <= 0:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    with get_db() as conn:
        conn.execute("INSERT INTO services (business_id, name, description, price) VALUES (?,?,?,?)",
                     (BUSINESS_ID, name, description, price))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price = float(data.get('price', 0))
    if not name or price <= 0:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    with get_db() as conn:
        conn.execute("UPDATE services SET name=?, description=?, price=? WHERE id=? AND business_id=?",
                     (name, description, price, service_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    with get_db() as conn:
        conn.execute("UPDATE services SET is_active=0 WHERE id=? AND business_id=?", (service_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

# ---------- Tax ----------
@app.route('/api/taxrate', methods=['GET'])
def get_tax_rate():
    with get_db() as conn:
        row = conn.execute("SELECT tax_rate FROM tax_settings WHERE business_id=? ORDER BY id DESC LIMIT 1", (BUSINESS_ID,)).fetchone()
        return jsonify({'rate': row['tax_rate'] if row else 8})

@app.route('/api/taxrate', methods=['POST'])
def set_tax_rate():
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    tax_rate = float(data.get('tax_rate', 8))
    with get_db() as conn:
        conn.execute("INSERT INTO tax_settings (business_id, tax_rate, updated_at) VALUES (?,?,?)",
                     (BUSINESS_ID, tax_rate, datetime.datetime.now().isoformat()))
        conn.commit()
    return jsonify({'success': True})

# ---------- Orders ----------
@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip().lower()
    service_id = data.get('service_id')
    item_desc = data.get('item_description', '').strip()
    collection_date = data.get('collection_date')
    subtotal = float(data.get('subtotal', 0))
    
    if not all([name, phone, collection_date, service_id]) or subtotal <= 0:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    order_code = f"CTX{random.randint(100000, 999999)}{int(datetime.datetime.now().timestamp())}"
    date_taken = datetime.date.today().isoformat()
    user_id = session.get('user_id', None)
    
    with get_db() as conn:
        tax_row = conn.execute("SELECT tax_rate FROM tax_settings WHERE business_id=? ORDER BY id DESC LIMIT 1", (BUSINESS_ID,)).fetchone()
        tax_rate = tax_row['tax_rate'] if tax_row else 8
        tax_amount = subtotal * tax_rate / 100
        total = subtotal + tax_amount
        
        conn.execute('''INSERT INTO orders 
                        (business_id, user_id, service_id, item_description, date_taken, collection_date, 
                         subtotal, tax_rate, tax_amount, total, status, payment_status,
                         client_name, client_phone, client_email, order_code)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                     (BUSINESS_ID, user_id, service_id, item_desc, date_taken, collection_date,
                      subtotal, tax_rate, tax_amount, total, 'received', 'pending',
                      name, phone, email, order_code))
        conn.commit()
        return jsonify({
            'success': True,
            'order_id': conn.execute("SELECT last_insert_rowid()").fetchone()[0],
            'order_code': order_code,
            'subtotal': subtotal,
            'tax': tax_amount,
            'total': total,
            'message': 'Order created. Use payment panel to pay.'
        })

@app.route('/api/order/<order_code>')
def get_order(order_code):
    with get_db() as conn:
        row = conn.execute('''SELECT orders.*, services.name as service_name
                              FROM orders 
                              LEFT JOIN services ON orders.service_id = services.id
                              WHERE orders.order_code = ? AND orders.business_id = ?''', 
                           (order_code, BUSINESS_ID)).fetchone()
        if row:
            return jsonify(dict(row))
        return jsonify({'error': 'Order not found'}), 404

# ---------- Customer Portal ----------
@app.route('/api/my-orders', methods=['GET'])
def my_orders():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    user_id = session['user_id']
    with get_db() as conn:
        rows = conn.execute('''SELECT orders.*, services.name as service_name
                               FROM orders 
                               LEFT JOIN services ON orders.service_id = services.id
                               WHERE orders.user_id = ? AND orders.business_id = ?
                               ORDER BY orders.id DESC''', (user_id, BUSINESS_ID)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/customer-complaint', methods=['POST'])
def customer_complaint():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    data = request.json
    order_id = data.get('order_id')
    complaint_text = data.get('complaint_text', '').strip()
    user_id = session['user_id']
    
    if not order_id or not complaint_text:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    
    with get_db() as conn:
        order = conn.execute('''SELECT id FROM orders 
                                 WHERE id=? AND user_id=? AND business_id=?''',
                             (order_id, user_id, BUSINESS_ID)).fetchone()
        if not order:
            return jsonify({'success': False, 'error': 'Order not found or not yours'}), 404
        
        conn.execute("INSERT INTO complaints (business_id, order_id, user_id, complaint_text, status, created_at) VALUES (?,?,?,?,?,?)",
                     (BUSINESS_ID, order_id, user_id, complaint_text, 'open', datetime.datetime.now().isoformat()))
        conn.commit()
        return jsonify({'success': True})

@app.route('/api/mpesa-payment', methods=['POST'])
def mpesa_payment():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    data = request.json
    order_code = data.get('order_code')
    phone = data.get('phone', '').strip()
    amount = float(data.get('amount', 0))
    user_id = session['user_id']
    
    if not order_code or not phone or amount <= 0:
        return jsonify({'success': False, 'error': 'Order code, phone and amount required'}), 400
    
    with get_db() as conn:
        order = conn.execute('''SELECT * FROM orders
                                 WHERE order_code=? AND user_id=? AND business_id=?''',
                             (order_code, user_id, BUSINESS_ID)).fetchone()
        if not order:
            return jsonify({'success': False, 'error': 'Order not found or not yours'}), 404
        
        print(f"[M-Pesa Demo] STK Push to {phone} for KES {amount:.2f} - Order {order_code}")
        conn.execute("UPDATE orders SET payment_status='paid' WHERE id=?", (order['id'],))
        conn.commit()
        return jsonify({'success': True, 'message': f'Payment of KES {amount:.2f} received for order {order_code}'})

# ---------- Admin Data ----------
@app.route('/api/users', methods=['GET'])
def get_all_users():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        rows = conn.execute("SELECT id, username, email, full_name, phone, role, is_active, created_at FROM users WHERE business_id=? ORDER BY id DESC", (BUSINESS_ID,)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/workers', methods=['GET'])
def get_workers():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM workers WHERE business_id=?", (BUSINESS_ID,)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/workers', methods=['POST'])
def add_worker():
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    phone = data.get('phone', '').strip()
    wage = float(data.get('wage', 0))
    hire_date = datetime.date.today().isoformat()
    if not name:
        return jsonify({'success': False, 'error': 'Name required'}), 400
    with get_db() as conn:
        conn.execute("INSERT INTO workers (business_id, name, role, phone, wage, hire_date) VALUES (?,?,?,?,?,?)",
                     (BUSINESS_ID, name, role, phone, wage, hire_date))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/workers/<int:worker_id>', methods=['PUT'])
def update_worker(worker_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    phone = data.get('phone', '').strip()
    wage = float(data.get('wage', 0))
    with get_db() as conn:
        conn.execute("UPDATE workers SET name=?, role=?, phone=?, wage=? WHERE id=? AND business_id=?",
                     (name, role, phone, wage, worker_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/workers/<int:worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    with get_db() as conn:
        conn.execute("DELETE FROM workers WHERE id=? AND business_id=?", (worker_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/machines', methods=['GET'])
def get_machines():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM machines WHERE business_id=?", (BUSINESS_ID,)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/machines', methods=['POST'])
def add_machine():
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    name = data.get('name', '').strip()
    type_ = data.get('type', '').strip()
    status = data.get('status', 'Operational').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name required'}), 400
    with get_db() as conn:
        conn.execute("INSERT INTO machines (business_id, name, type, status) VALUES (?,?,?,?)",
                     (BUSINESS_ID, name, type_, status))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/machines/<int:machine_id>', methods=['PUT'])
def update_machine(machine_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    name = data.get('name', '').strip()
    type_ = data.get('type', '').strip()
    status = data.get('status', '').strip()
    with get_db() as conn:
        conn.execute("UPDATE machines SET name=?, type=?, status=? WHERE id=? AND business_id=?",
                     (name, type_, status, machine_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/machines/<int:machine_id>', methods=['DELETE'])
def delete_machine(machine_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    with get_db() as conn:
        conn.execute("DELETE FROM machines WHERE id=? AND business_id=?", (machine_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/financials', methods=['GET'])
def financials():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        row = conn.execute('''SELECT 
                                COALESCE(SUM(total), 0) as total_revenue, 
                                COUNT(*) as total_orders, 
                                COALESCE(SUM(CASE WHEN payment_status='paid' THEN total ELSE 0 END), 0) as collected,
                                COALESCE(SUM(CASE WHEN payment_status='pending' THEN total ELSE 0 END), 0) as pending
                              FROM orders WHERE business_id=?''', (BUSINESS_ID,)).fetchone()
        return jsonify({
            'total_revenue': row['total_revenue'] or 0,
            'total_orders': row['total_orders'] or 0,
            'collected': row['collected'] or 0,
            'pending': row['pending'] or 0
        })

@app.route('/api/complaints', methods=['GET'])
def get_complaints():
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        rows = conn.execute('''SELECT complaints.*, orders.client_name, orders.item_description
                               FROM complaints 
                               JOIN orders ON complaints.order_id = orders.id 
                               WHERE complaints.business_id = ?
                               ORDER BY complaints.created_at DESC''', (BUSINESS_ID,)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/complaints', methods=['POST'])
def add_complaint_admin():
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    order_id = data.get('order_id')
    complaint_text = data.get('complaint_text', '').strip()
    if not order_id or not complaint_text:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    with get_db() as conn:
        conn.execute("INSERT INTO complaints (business_id, order_id, complaint_text, status, created_at) VALUES (?,?,?,?,?)",
                     (BUSINESS_ID, order_id, complaint_text, 'open', datetime.datetime.now().isoformat()))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/complaints/<int:complaint_id>/reply', methods=['POST'])
def reply_complaint(complaint_id):
    if not admin_required():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.json
    reply = data.get('reply', '').strip()
    if not reply:
        return jsonify({'success': False, 'error': 'Reply required'}), 400
    with get_db() as conn:
        conn.execute("UPDATE complaints SET reply=?, status='replied' WHERE id=? AND business_id=?",
                     (reply, complaint_id, BUSINESS_ID))
        conn.commit()
    return jsonify({'success': True})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')