from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

auth = Blueprint('auth', __name__)

# Hardcoded credentials
ADMIN_USERNAME = "Admin"
ADMIN_PASSWORD = "Admin@123"


def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard.index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    # If already logged in, redirect to dashboard
    if 'logged_in' in session:
        return redirect(url_for('dashboard.index'))
    
    return render_template('login.html')


@auth.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('auth.login'))
