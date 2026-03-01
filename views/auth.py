from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models import User, StudentProfile, CompanyProfile

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'company':
            return redirect(url_for('company.dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
            
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
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'company':
                return redirect(url_for('company.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
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
        
        # Now create student profile
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
        
        # Now create company profile
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
