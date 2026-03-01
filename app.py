from flask import Flask, render_template, redirect, url_for, flash
from config import Config
from extensions import db, login_manager, bcrypt
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from views.auth import auth_bp
from views.admin import admin_bp
from views.company import company_bp
from views.student import student_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(student_bp, url_prefix='/student')
    
    @app.route('/')
    def index():
        return render_template('index.html')
        
    # Check if admin exists, if not create one
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
