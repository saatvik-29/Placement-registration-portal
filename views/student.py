from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import PlacementDrive, Application
from views.utils import role_required
import os
from werkzeug.utils import secure_filename
from flask import current_app

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
    # Only approved drives, maybe also not past deadline, but let's keep it simple
    drives = PlacementDrive.query.filter_by(status='approved').all()
    # Get applied drive IDs to disable apply button
    applied_drives = [app.drive_id for app in current_user.student_profile.applications]
    return render_template('student/drives.html', drives=drives, applied_drives=applied_drives)

@student_bp.route('/apply/<int:drive_id>', methods=['POST'])
@login_required
@role_required('student')
def apply_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != 'approved':
        flash("You can only apply to approved drives.", "danger")
        return redirect(url_for('student.available_drives'))
        
    # Check if already applied
    existing_application = Application.query.filter_by(
        student_id=current_user.student_profile.id, 
        drive_id=drive_id
    ).first()
    
    if existing_application:
        flash("You have already applied to this drive.", "warning")
        return redirect(url_for('student.available_drives'))
        
    new_application = Application(
        student_id=current_user.student_profile.id,
        drive_id=drive_id,
        status='applied'
    )
    db.session.add(new_application)
    db.session.commit()
    flash(f"Successfully applied for {drive.job_title} at {drive.company.company_name}.", "success")
    return redirect(url_for('student.dashboard'))

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        resume = request.files.get('resume')
        
        current_user.student_profile.name = name
        current_user.student_profile.contact = contact
        
        if resume and resume.filename != '':
            filename = secure_filename(resume.filename)
            # Create unique filename
            filename = f"user_{current_user.id}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resume.save(filepath)
            current_user.student_profile.resume_filename = filename
            
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('student.profile'))
        
    return render_template('student/profile.html')
