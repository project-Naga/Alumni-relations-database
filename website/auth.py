from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import Users, Admins
from .import oauth
from . import db
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import re
import os
auth = Blueprint('auth', __name__)
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        email = re.sub('<[^>]*>', '', email)
        password = request.form.get('password')
        password = re.sub('<[^>]*>', '', password)
        
        user = Users.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                flash('Logged in Successfully!', category="success")
                login_user(user, remember=True)
                return redirect(url_for('views.profile'))
            else:
                flash("Incorrect password, try again.", category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template('login.html', user=current_user,usertype="User")

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged Out Succesfully",'success')
    return redirect(url_for('views.index'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        email = re.sub('<[^>]*>', '', email)
        user_name = request.form.get('user_name')
        user_name = re.sub('<[^>]*>', '', user_name)
        password1 = request.form.get('password1')
        password1 = re.sub('<[^>]*>', '', password1)
        password2 = request.form.get('password2')
        password2 = re.sub('<[^>]*>', '', password2)
        
        user = Users.query.filter_by(email=email).first()
        if user:
            flash("Email already exists", category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(user_name)< 2:
            flash('Name must be greater than 1 characters.', category='error')
        elif password1 != password2:
            flash('Passwords dont match', category='error')
        elif len(password1) < 7:
            flash('Passwords must be atleast 7 characters.', category='error')
        else:
            new_user = Users( user_name=user_name, email=email, password=generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.profile'))

    return render_template("sign_up.html",user=current_user,usertype="User")

@auth.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_email = request.form.get('admin_email')
        admin_email = re.sub('<[^>]*>', '', admin_email)
        password = request.form.get('password')
        password = re.sub('<[^>]*>', '', password)

        admin = Admins.query.filter_by(admin_email=admin_email).first()
        if admin:
            if check_password_hash(admin.password,password):
                flash('Logged in Successfully!', category="success")
                login_user(admin, remember=True)
                return redirect(url_for('views.display'))
            else:
                flash("Incorrect password, try again.", category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template('admin_login.html', user=current_user,usertype="Admin")


@auth.route('/googleauth')
def googleauth():
    return render_template('googleauth.html')
 
@auth.route('/google/')
def google():
     
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id="", #Add your Client ID
        client_secret="", #Add your Client secret
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    redirect_uri = url_for('auth.google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth.route('/admin_google/')
def admin_google():
   
     
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google1',
        client_id="", #Add your Client ID
        client_secret="", #Add your Client secret
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
     
    # Redirect to google_auth function
    redirect_uri = url_for('auth.admin_google_auth', _external=True)
    return oauth.google1.authorize_redirect(redirect_uri)

@auth.route('/google/auth')
def google_auth():
    token = oauth.google.authorize_access_token()
    nonce = session.get('oauth_nonce')  # Retrieve the stored nonce
    user_info = oauth.google.parse_id_token(token,nonce = nonce)
    print("Google User:", user_info)
    
    # Retrieve or create the user in your database based on Google user information
    email = user_info.get('email')
    google_id = user_info.get('sub')
    name = user_info.get('name')
    user = Users.query.filter_by(email=email).first()
    if not user:
        # Create a new user
        user = Users(email=email, user_name=name)
        db.session.add(user)
        db.session.commit()
        
    
    # Log in the user
    login_user(user)
    flash("Login Successful", category='success')
    # Redirect to /display
    return redirect(url_for('views.profile'))


@auth.route('/admin_google/auth/')
def admin_google_auth():
    token = oauth.google1.authorize_access_token()
    nonce = session.get('oauth_nonce')  # Retrieve the stored nonce
    user_info = oauth.google1.parse_id_token(token, nonce=nonce)
    print("Google User:", user_info)
    
    # Retrieve or create the user in your database based on Google user information
    email = user_info.get('email')
    google_id = user_info.get('sub')
    
    # Retrieve existing user or create new user
    user = Admins.query.filter_by(admin_email=email).first()
    if not user:
        flash("This gmail is not an admin account. Please recheck", category='error')
        return render_template("admin_login.html", user=current_user,usertype="Admin")
    login_user(user)
    flash("Login successful", 'success')
    return redirect(url_for('views.display'))


