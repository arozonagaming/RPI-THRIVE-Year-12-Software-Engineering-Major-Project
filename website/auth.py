from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User, Plant
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .views import start_background_thread

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                start_background_thread(current_app, user.id)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    user_plants = Plant.query.filter_by(user_id=current_user.id).first_or_404()
    user_plants.system_status = "Not Connected"
    db.session.commit()
    logout_user()
    return redirect(url_for('auth.login'))