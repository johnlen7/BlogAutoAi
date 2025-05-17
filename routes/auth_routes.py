import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        
        # Check if username or email already exists
        if not error:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = f'Username {username} is already registered.'
            
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                error = f'Email {email} is already registered.'
        
        # Create new user if no errors
        if not error:
            # Hash password and create user
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )
            
            # Add to database
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"New user registered: {username}")
            
            # Flash success message and redirect to login
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        # Flash error message if any
        flash(error, 'danger')
    
    # Render registration form
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Validate form data
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        
        # Check credentials
        if not error:
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                error = 'Invalid username or password.'
        
        # Log user in if no errors
        if not error:
            login_user(user, remember=remember)
            logger.info(f"User logged in: {username}")
            
            # Get next page from URL parameters (for redirects from protected pages)
            next_page = request.args.get('next')
            
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
                
            flash('Login successful!', 'success')
            return redirect(next_page)
        
        # Flash error message if any
        flash(error, 'danger')
    
    # Render login form
    return render_template('login.html', now=datetime.now())

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    if request.method == 'POST':
        # Get form data
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        error = None
        
        if not current_password:
            error = 'Current password is required.'
        elif not check_password_hash(current_user.password_hash, current_password):
            error = 'Current password is incorrect.'
        elif not new_password:
            error = 'New password is required.'
        elif new_password != confirm_password:
            error = 'New passwords do not match.'
        
        # Update password if no errors
        if not error:
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            logger.info(f"User {current_user.username} updated password")
            flash('Password updated successfully!', 'success')
        else:
            flash(error, 'danger')
    
    # Render profile page
    return render_template('profile.html')
