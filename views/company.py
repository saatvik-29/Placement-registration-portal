from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import PlacementDrive, Application, StudentProfile
from views.utils import role_required

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
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        eligibility = request.form.get('eligibility')
        deadline = request.form.get('deadline')
        
        from datetime import datetime
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        except Exception:
            flash("Invalid date format.", "danger")
            return redirect(url_for('company.create_drive'))
            
        new_drive = PlacementDrive(
            company_id=current_user.company_profile.id,
            job_title=job_title,
            job_description=job_description,
            eligibility=eligibility,
            deadline=deadline_date,
            status='pending'
        )
        db.session.add(new_drive)
        db.session.commit()
        flash("Placement drive created and is pending admin approval.", "success")
        return redirect(url_for('company.dashboard'))
        
    return render_template('company/create_drive.html')

@company_bp.route('/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
@login_required
@role_required('company')
def edit_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('company.dashboard'))
        
    if request.method == 'POST':
        drive.job_title = request.form.get('job_title')
        drive.job_description = request.form.get('job_description')
        drive.eligibility = request.form.get('eligibility')
        deadline = request.form.get('deadline')
        
        from datetime import datetime
        try:
            drive.deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
        except:
            flash("Invalid date format.", "danger")
            return redirect(url_for('company.edit_drive', drive_id=drive_id))
            
        status = request.form.get('status')
        if status in ['closed']:
            drive.status = 'closed'
            
        db.session.commit()
        flash("Drive updated successfully.", "success")
        return redirect(url_for('company.dashboard'))
        
    return render_template('company/edit_drive.html', drive=drive)
    
@company_bp.route('/delete_drive/<int:drive_id>', methods=['POST'])
@login_required
@role_required('company')
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('company.dashboard'))
        
    db.session.delete(drive)
    db.session.commit()
    flash("Drive deleted successfully.", "success")
    return redirect(url_for('company.dashboard'))

@company_bp.route('/applicants/<int:drive_id>')
@login_required
@role_required('company')
def view_applicants(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.company_profile.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('company.dashboard'))
        
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template('company/view_applicants.html', drive=drive, applications=applications)

@company_bp.route('/update_application/<int:app_id>', methods=['POST'])
@login_required
@role_required('company')
def update_application(app_id):
    application = Application.query.get_or_404(app_id)
    if application.drive.company_id != current_user.company_profile.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('company.dashboard'))
        
    new_status = request.form.get('status')
    if new_status in ['shortlisted', 'selected', 'rejected']:
        application.status = new_status
        db.session.commit()
        flash(f"Application status updated to {new_status}.", "success")
    return redirect(url_for('company.view_applicants', drive_id=application.drive_id))
