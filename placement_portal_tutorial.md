# Placement Portal Application: Step-by-Step Build Guide

This guide walks you through building the Placement Portal Application from scratch. It is designed to be followed sequentially, allowing you to build the application module by module and make logical Git commits along the way.

---

## Step 1: Project Setup and Dependencies

First, create a new directory for your project and set up a virtual environment.

**1. Create the project structure:**
```bash
mkdir PlacementPortal
cd PlacementPortal
mkdir -p static/css static/uploads templates/admin templates/company templates/student views
touch views/__init__.py
```

**2. Create `requirements.txt`:**
Create this file in the root directory.

```text
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Bcrypt==1.0.1
Werkzeug==3.0.1
```

**3. Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> 💡 **Commit #1**: `Initial commit: Added project structure and requirements.txt`

---

## Step 2: Configuration and Extensions

**1. Create `config.py`:**
This file holds the configuration variables for Flask and SQLAlchemy.

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-placement-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///placement.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
```

**2. Create `extensions.py`:**
This separates the Flask extensions to avoid circular imports.

```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
```

> 💡 **Commit #2**: `Setup Flask configuration and extensions`

---

## Step 3: Database Models

**1. Create `models.py`:**
Define the database schema for Users, Profiles, Drives, and Applications.

```python
from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, company, student
    is_active = db.Column(db.Boolean, default=True) 
    
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade='all, delete-orphan')

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50))
    resume_filename = db.Column(db.String(150))
    applications = db.relationship('Application', backref='student', cascade='all, delete-orphan')

class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)
    drives = db.relationship('PlacementDrive', backref='company', cascade='all, delete-orphan')

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending') 
    applications = db.relationship('Application', backref='drive', cascade='all, delete-orphan')

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='applied') 
```

> 💡 **Commit #3**: `Implemented SQLAlchemy database models`

---

## Step 4: Core Application Factory + Base Templates

> ⚠️ **Important**: We create `app.py` AND the base templates (`layout.html` + `index.html`) **in the same step** so the app is immediately runnable after this commit. `app.py` renders `index.html` on the `/` route, so the template must exist before you run the server.

**1. Create `views/utils.py`:**
Add a custom decorator for role-based access control.

```python
from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            if not current_user.is_active:
                abort(403, description="Your account has been deactivated.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

**2. Create `app.py`:**
This is the main entry point. Blueprints will be registered in later steps — the `# placeholder` comments mark where they will go.

```python
from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, bcrypt
from models import User
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Blueprints registered here in later steps ---

    @app.route('/')
    def index():
        return render_template('index.html')

    # Programmatic DB creation + default admin
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            hashed_pwd = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(username='admin', password_hash=hashed_pwd, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin / admin123")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

**3. Create `templates/layout.html`:**
The base Jinja2 template using Bootstrap 5. All other templates will `extend` this.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Placement Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <!-- Add your custom CSS here later -->
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
  <div class="container">
    <a class="navbar-brand" href="{{ url_for('index') }}">Campus Connect</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto">
        {% if current_user.is_authenticated %}
            {% if current_user.role == 'admin' %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('admin.dashboard') }}">Dashboard</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('admin.manage_users') }}">Manage Users</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('admin.all_drives') }}">All Drives</a></li>
            {% elif current_user.role == 'company' %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('company.dashboard') }}">Dashboard</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('company.create_drive') }}">Create Drive</a></li>
            {% elif current_user.role == 'student' %}
                <li class="nav-item"><a class="nav-link" href="{{ url_for('student.dashboard') }}">Dashboard</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('student.available_drives') }}">Available Drives</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ url_for('student.profile') }}">Profile</a></li>
            {% endif %}
            <li class="nav-item">
                <span class="nav-link text-light fw-bold mx-2">Hi, {{ current_user.username }}</span>
            </li>
            <li class="nav-item">
                <a class="btn btn-outline-light ms-2" href="{{ url_for('auth.logout') }}">Logout</a>
            </li>
        {% else %}
            <li class="nav-item"><a class="nav-link" href="{{ url_for('auth.login') }}">Login</a></li>
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">Register</a>
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item" href="{{ url_for('auth.register_student') }}">As Student</a></li>
                    <li><a class="dropdown-item" href="{{ url_for('auth.register_company') }}">As Company</a></li>
                </ul>
            </li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>

<div class="container">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} alert-dismissible fade show">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

**4. Create `templates/index.html`:**

```html
{% extends "layout.html" %}

{% block content %}
<div class="container mt-5">
    <div class="p-5 mb-4 bg-light rounded-3">
        <h1 class="display-5 fw-bold">Campus Recruitment Portal</h1>
        <p class="col-md-8 fs-4">Connect students with top companies seamlessly.</p>
        <a href="{{ url_for('auth.register_student') }}" class="btn btn-primary btn-lg me-2">I'm a Student</a>
        <a href="{{ url_for('auth.register_company') }}" class="btn btn-outline-secondary btn-lg">I'm a Company</a>
    </div>
</div>
{% endblock %}
```

> 💡 **Commit #4**: `Setup Flask app factory, utils, base layout, and landing page`

> 🚀 **Run to verify**: `python app.py` → visit `http://localhost:5000`. You should see the landing page. The Login/Register links in the navbar will 404 for now (blueprints come next) — that is expected.

---

## Step 5: Authentication Routing

**1. Create `views/auth.py`:**
Handles login, logout, and registration logic.

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models import User, StudentProfile, CompanyProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin': return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'company': return redirect(url_for('company.dashboard'))
        elif current_user.role == 'student': return redirect(url_for('student.dashboard'))
            
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash("Account has been deactivated or blacklisted.", "danger")
                return redirect(url_for('auth.login'))
                
            if user.role == 'company' and not user.company_profile.is_approved:
                flash("Your company account is pending admin approval.", "warning")
                return redirect(url_for('auth.login'))
                
            login_user(user)
            if user.role == 'admin': return redirect(url_for('admin.dashboard'))
            elif user.role == 'company': return redirect(url_for('company.dashboard'))
            else: return redirect(url_for('student.dashboard'))
        else:
            flash("Invalid credentials.", "danger")
            
    return render_template('login.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        contact = request.form.get('contact')
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('auth.register_student'))
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_pw, role='student')
        db.session.add(new_user)
        db.session.commit()
        
        profile = StudentProfile(user_id=new_user.id, name=name, contact=contact)
        db.session.add(profile)
        db.session.commit()
        
        flash("Registration successful. You can now login.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('register_student.html')

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        hr_contact = request.form.get('hr_contact')
        website = request.form.get('website')
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('auth.register_company'))
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_pw, role='company')
        db.session.add(new_user)
        db.session.commit()
        
        profile = CompanyProfile(user_id=new_user.id, company_name=company_name, hr_contact=hr_contact, website=website)
        db.session.add(profile)
        db.session.commit()
        
        flash("Registration successful. Please wait for Admin approval before logging in.", "info")
        return redirect(url_for('auth.login'))
        
    return render_template('register_company.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
```

**2. Update `app.py`:**
Uncomment/add the imports and register the blueprints in the `create_app` function:
```python
# Add this import at the top
from views.auth import auth_bp

# Inside create_app(), right below load_user:
app.register_blueprint(auth_bp)
```

> 💡 **Commit #5**: `Added authentication and registration backend logic`

> 🚀 **Run to verify**: `python app.py` → the server starts. Login/Register routes are registered now but the form templates don't exist yet — they're added in Step 6.

---

## Step 6: Authentication Templates

> ℹ️ `layout.html` and `index.html` were already created in **Step 4**. This step only adds the auth form templates that the `auth_bp` blueprint (registered in Step 5) needs to render.

**1. Create `templates/login.html`:**

```html
{% extends "layout.html" %}
{% block content %}
<div class="row justify-content-center mt-5">
  <div class="col-md-5">
    <div class="card p-4">
      <h3 class="mb-3">Login</h3>
      <form method="POST">
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input type="text" name="username" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" name="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary w-100">Login</button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
```

**2. Create `templates/register_student.html`:**

```html
{% extends "layout.html" %}
{% block content %}
<div class="row justify-content-center mt-5">
  <div class="col-md-6">
    <div class="card p-4">
      <h3 class="mb-3">Register as Student</h3>
      <form method="POST">
        <div class="mb-3"><label class="form-label">Username</label>
          <input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Password</label>
          <input type="password" name="password" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Full Name</label>
          <input type="text" name="name" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Contact</label>
          <input type="text" name="contact" class="form-control"></div>
        <button type="submit" class="btn btn-primary w-100">Register</button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
```

**3. Create `templates/register_company.html`:**

```html
{% extends "layout.html" %}
{% block content %}
<div class="row justify-content-center mt-5">
  <div class="col-md-6">
    <div class="card p-4">
      <h3 class="mb-3">Register as Company</h3>
      <form method="POST">
        <div class="mb-3"><label class="form-label">Username</label>
          <input type="text" name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Password</label>
          <input type="password" name="password" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Company Name</label>
          <input type="text" name="company_name" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">HR Contact</label>
          <input type="text" name="hr_contact" class="form-control"></div>
        <div class="mb-3"><label class="form-label">Website</label>
          <input type="text" name="website" class="form-control"></div>
        <button type="submit" class="btn btn-primary w-100">Register</button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
```

> 💡 **Commit #6**: `Added authentication form templates (login, register student, register company)`

> 🚀 **Run to verify**: `python app.py` → visit `http://localhost:5000/login`, `/register/student`, `/register/company`. Forms should render and submission should work.

---

## Step 7: Admin Module

**1. Create `views/admin.py`:**
Handles approving companies, managing accounts, and overseeing placement drives.

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from views.utils import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_companies = User.query.filter_by(role='company').count()
    total_applications = Application.query.count()
    total_drives = PlacementDrive.query.count()
    
    pending_companies = CompanyProfile.query.filter_by(is_approved=False).all()
    pending_drives = PlacementDrive.query.filter_by(status='pending').all()
    
    return render_template('admin/dashboard.html', 
                           total_students=total_students, 
                           total_companies=total_companies,
                           total_applications=total_applications,
                           total_drives=total_drives,
                           pending_companies=pending_companies,
                           pending_drives=pending_drives)

@admin_bp.route('/approve_company/<int:profile_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_company(profile_id):
    action = request.form.get('action')
    company = CompanyProfile.query.get_or_404(profile_id)
    if action == 'approve':
        company.is_approved = True
        flash(f"Company {company.company_name} approved.", "success")
    elif action == 'reject':
        user = company.user
        db.session.delete(company)
        db.session.delete(user)
        flash("Company application rejected and removed.", "info")
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/approve_drive/<int:drive_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_drive(drive_id):
    action = request.form.get('action')
    drive = PlacementDrive.query.get_or_404(drive_id)
    if action == 'approve':
        drive.status = 'approved'
        flash("Drive approved.", "success")
    elif action == 'reject':
        drive.status = 'rejected'
        flash("Placement drive rejected.", "info")
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/manage_users', methods=['GET'])
@login_required
@role_required('admin')
def manage_users():
    search_query = request.args.get('search', '')
    if search_query:
        students = StudentProfile.query.filter(StudentProfile.name.ilike(f'%{search_query}%')).all()
        companies = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f'%{search_query}%')).all()
    else:
        students = StudentProfile.query.all()
        companies = CompanyProfile.query.all()
    return render_template('admin/manage_users.html', students=students, companies=companies, search_query=search_query)

@admin_bp.route('/toggle_status/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def toggle_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        user.is_active = not user.is_active
        db.session.commit()
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin.manage_users'))
    
@admin_bp.route('/all_drives')
@login_required
@role_required('admin')
def all_drives():
    drives = PlacementDrive.query.all()
    return render_template('admin/all_drives.html', drives=drives)
    
@admin_bp.route('/drive/<int:drive_id>/applications')
@login_required
@role_required('admin')
def drive_applications(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = Application.query.filter_by(drive_id=drive.id).all()
    return render_template('admin/applications.html', drive=drive, applications=applications)
```

**2. Update `app.py`:** Add the Blueprint.
```python
from views.admin import admin_bp

# Inside create_app()
app.register_blueprint(admin_bp, url_prefix='/admin')
```

**3. Admins Templates:**
- `templates/admin/dashboard.html` (Use a table logic looping `pending_companies` and `pending_drives` returning 'approve' and 'reject' form POST requests)
- `templates/admin/manage_users.html` (Iterates and displays all users with a status toggle/delete)

> 💡 **Commit #7**: `Added Admin role features: user moderation and drive approvals`

> 🚀 **Run to verify**: `python app.py` → Login as `admin / admin123`. You should be redirected to `/admin/dashboard`.

---

## Step 8: Company Module

**1. Create `views/company.py`:**
Handles creating and updating placement drives, and managing student applications.

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import PlacementDrive, Application
from views.utils import role_required
from datetime import datetime

company_bp = Blueprint('company', __name__)

@company_bp.route('/dashboard')
@login_required
@role_required('company')
def dashboard():
    drives = PlacementDrive.query.filter_by(company_id=current_user.company_profile.id).all()
    return render_template('company/dashboard.html', drives=drives)

@company_bp.route('/create_drive', methods=['GET', 'POST'])
@login_required
@role_required('company')
def create_drive():
    if request.method == 'POST':
        new_drive = PlacementDrive(
            company_id=current_user.company_profile.id,
            job_title=request.form.get('job_title'),
            job_description=request.form.get('job_description'),
            eligibility=request.form.get('eligibility'),
            deadline=datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date(),
            status='pending'
        )
        db.session.add(new_drive)
        db.session.commit()
        flash("Drive created and pending approval.", "success")
        return redirect(url_for('company.dashboard'))
    return render_template('company/create_drive.html')

@company_bp.route('/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
@login_required
@role_required('company')
def edit_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id: abort(403)
        
    if request.method == 'POST':
        drive.job_title = request.form.get('job_title')
        drive.job_description = request.form.get('job_description')
        drive.eligibility = request.form.get('eligibility')
        drive.deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date()
        status = request.form.get('status')
        if status in ['closed']:
            drive.status = 'closed'
            
        db.session.commit()
        return redirect(url_for('company.dashboard'))
    return render_template('company/edit_drive.html', drive=drive)

@company_bp.route('/delete_drive/<int:drive_id>', methods=['POST'])
@login_required
@role_required('company')
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id == current_user.company_profile.id:
        db.session.delete(drive)
        db.session.commit()
    return redirect(url_for('company.dashboard'))

@company_bp.route('/applicants/<int:drive_id>')
@login_required
@role_required('company')
def view_applicants(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template('company/view_applicants.html', drive=drive, applications=applications)

@company_bp.route('/update_application/<int:app_id>', methods=['POST'])
@login_required
@role_required('company')
def update_application(app_id):
    application = Application.query.get_or_404(app_id)
    new_status = request.form.get('status')
    if new_status in ['shortlisted', 'selected', 'rejected']:
        application.status = new_status
        db.session.commit()
    return redirect(url_for('company.view_applicants', drive_id=application.drive_id))
```

**2. Update `app.py`:** Add the Blueprint.
```python
from views.company import company_bp

# Inside create_app()
app.register_blueprint(company_bp, url_prefix='/company')
```

**3. Company Templates:**
Construct Forms for creating (`templates/company/create_drive.html`) & editing (`templates/company/edit_drive.html`), ensuring the `<form>` `action` is wired seamlessly back into the variables required by `views/company.py`.

> 💡 **Commit #8**: `Built Company features: creating drives and adjusting applicant status`

> 🚀 **Run to verify**: `python app.py` → Register a company, get approved by admin, then login and create a drive.

---

## Step 9: Student Module

**1. Create `views/student.py`:**
Handles listing approved placement drives, saving applications, and managing student profiles.

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import PlacementDrive, Application
from views.utils import role_required
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    applications = Application.query.filter_by(student_id=current_user.student_profile.id).all()
    return render_template('student/dashboard.html', applications=applications)

@student_bp.route('/drives')
@login_required
@role_required('student')
def available_drives():
    drives = PlacementDrive.query.filter_by(status='approved').all()
    applied_drives = [app.drive_id for app in current_user.student_profile.applications]
    return render_template('student/drives.html', drives=drives, applied_drives=applied_drives)

@student_bp.route('/apply/<int:drive_id>', methods=['POST'])
@login_required
@role_required('student')
def apply_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != 'approved': return redirect(url_for('student.available_drives'))
        
    existing_application = Application.query.filter_by(
        student_id=current_user.student_profile.id, drive_id=drive_id).first()
    
    if not existing_application:
        new_app = Application(student_id=current_user.student_profile.id, drive_id=drive_id, status='applied')
        db.session.add(new_app)
        db.session.commit()
    return redirect(url_for('student.dashboard'))

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    if request.method == 'POST':
        current_user.student_profile.name = request.form.get('name')
        current_user.student_profile.contact = request.form.get('contact')
        
        resume = request.files.get('resume')
        if resume and resume.filename != '':
            filename = f"user_{current_user.id}_{secure_filename(resume.filename)}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resume.save(filepath)
            current_user.student_profile.resume_filename = filename
            
        db.session.commit()
        return redirect(url_for('student.profile'))
        
    return render_template('student/profile.html')
```

**2. Update `app.py`:** Add the Blueprint.
```python
from views.student import student_bp

# Inside create_app()
app.register_blueprint(student_bp, url_prefix='/student')
```

**3. Student Templates:**
- `templates/student/dashboard.html`: Display history in a table.
- `templates/student/drives.html`: Foreach loop representing cards of `drives`. Check if `drive.id in applied_drives` to disable application.
- `templates/student/profile.html`: Utilize `enctype="multipart/form-data"` in form to submit the resume properly.

> 💡 **Commit #9**: `Added Student module: driving job application mechanics and profile setup`

> 🚀 **Run to verify**: `python app.py` → Register as a student, login, and apply to an approved drive.

---

## Step 10: Running Your Application

With all modules assembled, your `app.py` encapsulates everything nicely.

1. Ensure your Virtual Environment is active.
2. Ensure you have the uploads directory: `mkdir -p static/uploads`
3. Hit `python app.py`

When the app runs the first time, the `create_app()` lifecycle will automatically construct the SQLite tables (`placement.db` is dropped into `instance/` or root) AND it injects an **Admin user** (`admin` with password `admin123`). 

✅ **Final Commit Check**: Open your browser at `http://localhost:5000` to browse!
