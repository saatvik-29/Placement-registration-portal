from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
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
    action = request.form.get('action') # approve or reject
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
        flash(f"Drive for {drive.job_title} approved.", "success")
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
    if user.role == 'admin':
        flash("Action not permitted on admins.", "danger")
        return redirect(url_for('admin.manage_users'))
        
    user.is_active = not user.is_active
    status = "activated" if user.is_active else "deactivated"
    db.session.commit()
    flash(f"User {user.username} {status}.", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Cannot delete admin.", "danger")
        return redirect(url_for('admin.manage_users'))
        
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
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
