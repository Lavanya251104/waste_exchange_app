from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'
DATABASE = 'waste_exchange.db'

# ---------------- SIMPLE AI MATCH RULES ----------------
WASTE_MATCHES = {
    'plastic': ['Recycling Industry A', 'Recycling Industry B'],
    'metal': ['Metal Works Inc.', 'Metal Recycler Ltd.'],
    'paper': ['Paper Recycling Co.'],
    'glass': ['Glass Recycling Ltd.'],
}

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    results = cur.fetchall()
    cur.close()
    return (results[0] if results else None) if one else results

# ---------------- DATABASE INIT ----------------
def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            with open('schema.sql', 'r') as f:
                db.executescript(f.read())
            db.commit()
            print("✅ Database & Tables Created Successfully!")

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form['role']
        waste_types = request.form.get('waste_types', '').strip()  # New field

        if not username or not email or not password or role not in ('buyer', 'seller'):
            flash('Please fill all fields correctly.')
            return redirect(url_for('register'))

        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, email, password, role, waste_types) VALUES (?, ?, ?, ?, ?)',
                (username, email, generate_password_hash(password), role, waste_types)
            )
            db.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or Email already exists.')
            return redirect(url_for('register'))

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    if role == 'seller':
        wastes = query_db('SELECT * FROM waste WHERE user_id = ?', [user_id])
        requests_ = query_db('''
            SELECT r.request_id, r.status, u.username AS buyer_name, w.type, w.quantity
            FROM requests r
            JOIN users u ON r.buyer_id = u.user_id
            JOIN waste w ON r.waste_id = w.waste_id
            WHERE w.user_id = ?
            ORDER BY r.request_id DESC
        ''', [user_id])
        return render_template('dashboard.html', wastes=wastes, requests=requests_, role=role)

    else:
        # ---------------- BUYER LOGIC WITH PREFERENCES ----------------
        buyer = query_db('SELECT * FROM users WHERE user_id=?', [user_id], one=True)
        buyer_types = [t.strip().lower() for t in buyer['waste_types'].split(',')] if buyer['waste_types'] else []

        if buyer_types:
            placeholders = ','.join(['?']*len(buyer_types))
            wastes = query_db(f'''
                SELECT w.*, u.username AS seller_name
                FROM waste w
                JOIN users u ON w.user_id = u.user_id
                WHERE LOWER(w.type) IN ({placeholders})
                ORDER BY w.waste_id DESC
            ''', buyer_types)
        else:
            # Show all wastes if buyer has no preferences
            wastes = query_db('''
                SELECT w.*, u.username AS seller_name
                FROM waste w
                JOIN users u ON w.user_id = u.user_id
                ORDER BY w.waste_id DESC
            ''')

        requests_ = query_db('''
            SELECT r.*, w.type, w.quantity, u.username AS seller_name
            FROM requests r
            JOIN waste w ON r.waste_id = w.waste_id
            JOIN users u ON w.user_id = u.user_id
            WHERE r.buyer_id = ?
            ORDER BY r.request_id DESC
        ''', [user_id])

        return render_template('dashboard.html', wastes=wastes, requests=requests_, role=role)

# ---------------- ADD WASTE ----------------
@app.route('/add_waste', methods=['GET', 'POST'])
def add_waste():
    if 'user_id' not in session or session['role'] != 'seller':
        return redirect(url_for('login'))

    if request.method == 'POST':
        wtype = request.form['type'].strip()
        quantity = request.form['quantity']
        description = request.form['description'].strip()

        if not wtype or not quantity.isdigit():
            flash('Enter valid waste type and quantity.')
            return redirect(url_for('add_waste'))

        db = get_db()
        db.execute(
            'INSERT INTO waste (user_id, type, quantity, description) VALUES (?, ?, ?, ?)',
            (session['user_id'], wtype, int(quantity), description)
        )
        db.commit()
        flash('Waste added successfully.')
        return redirect(url_for('dashboard'))

    return render_template('add_waste.html')

# ---------------- CREATE REQUEST ----------------
@app.route('/create_request/<int:waste_id>', methods=['POST'])
def create_request(waste_id):
    if 'user_id' not in session or session['role'] != 'buyer':
        flash("Only buyers can request waste.")
        return redirect(url_for('login'))

    waste = query_db('SELECT * FROM waste WHERE waste_id = ?', [waste_id], one=True)
    if not waste:
        flash('Waste not found.')
        return redirect(url_for('dashboard'))

    db = get_db()
    existing = query_db('SELECT * FROM requests WHERE buyer_id=? AND waste_id=?',
                        [session['user_id'], waste_id], one=True)
    if existing:
        flash('You have already requested this waste.')
        return redirect(url_for('dashboard'))

    db.execute('INSERT INTO requests (buyer_id, waste_id) VALUES (?, ?)',
               (session['user_id'], waste_id))
    db.commit()
    flash(f"Request sent to seller for '{waste['type']}'!")
    return redirect(url_for('dashboard'))

# ---------------- HANDLE REQUEST ----------------
@app.route('/handle_request/<int:request_id>/<action>', methods=['POST'])
def handle_request(request_id, action):
    if 'user_id' not in session or session['role'] != 'seller':
        flash("Only sellers can respond to requests.")
        return redirect(url_for('login'))

    if action not in ('accept', 'deny'):
        flash("Invalid action.")
        return redirect(url_for('dashboard'))

    db = get_db()
    db.execute('UPDATE requests SET status=? WHERE request_id=?',
               (action, request_id))
    db.commit()
    flash(f"Request {action}ed successfully.")
    return redirect(url_for('dashboard'))

# ---------------- AI MATCH ----------------
@app.route('/ai_match')
def ai_match():
    if 'user_id' not in session or session['role'] != 'buyer':
        return redirect(url_for('login'))

    # Personalized AI match based on buyer's preferred waste types
    buyer = query_db('SELECT * FROM users WHERE user_id=?', [session['user_id']], one=True)
    buyer_types = [t.strip().lower() for t in buyer['waste_types'].split(',')] if buyer['waste_types'] else []

    matches = []
    for wtype in buyer_types:
        industries = WASTE_MATCHES.get(wtype, ['No matching industry found'])
        matches.append({'waste_type': wtype.capitalize(), 'industries': industries})

    return render_template('ai_match.html', matches=matches)

# ---------------- MAIN ----------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)