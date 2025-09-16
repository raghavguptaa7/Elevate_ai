from flask import Flask, render_template, request, redirect, session
import os
import re
from blueprints.career import career_bp
from blueprints.study import study_bp
import sqlite3
from utils.error_handlers import register_error_handlers
from utils.config import get_config, validate_config
from utils.logger import get_logger, log_info, log_error

# Initialize logger
logger = get_logger()

# Create Flask app
app = Flask(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# Email validation function
def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Validate configuration
is_valid, error_message = validate_config()
if not is_valid:
    log_error(f"Configuration error: {error_message}")
    raise RuntimeError(f"Configuration error: {error_message}")

# Register blueprints
app.register_blueprint(career_bp, url_prefix='/career')
app.register_blueprint(study_bp, url_prefix='/study')

log_info("Blueprints registered successfully")

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('login.html', error='Please provide both email and password')
        
        # Simple authentication for demo purposes
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[2] == password:  # Simple password check (not secure for production)
            session['user_id'] = user[0]
            session['email'] = user[1]
            return redirect('/')
        else:
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not email or not password or not confirm_password:
            return render_template('register.html', error='Please fill all fields')
        
        if not validate_email(email):
            return render_template('register.html', error='Please enter a valid email')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        # Check if user already exists
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return render_template('register.html', error='Email already registered')
        
        # Create new user
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        # Log in the new user
        session['user_id'] = user_id
        session['email'] = email
        
        return redirect('/')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Ensure database directory exists
os.makedirs('database', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# Initialize database
def init_db():
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create tables for career module
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        resume_text TEXT,
        job_description TEXT,
        analysis_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        job_title TEXT,
        questions TEXT,
        answers TEXT,
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create tables for study module
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS syllabi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        syllabus_id INTEGER,
        questions TEXT,
        answers TEXT,
        score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (syllabus_id) REFERENCES syllabi (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        syllabus_id INTEGER,
        plan_content TEXT,
        start_date DATE,
        end_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (syllabus_id) REFERENCES syllabi (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        syllabus_id INTEGER,
        topic TEXT,
        status TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (syllabus_id) REFERENCES syllabi (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()
log_info("Database initialized successfully")

# Register error handlers
register_error_handlers(app)
log_info("Error handlers registered successfully")

#
# --- The entire block of duplicate routes from here was removed ---
#

if __name__ == '__main__':
    log_info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)