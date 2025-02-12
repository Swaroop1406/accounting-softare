from flask import redirect, url_for, render_template, request, flash
from flask_login import UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

def init_auth(app, login_manager, storage):
    @login_manager.user_loader
    def load_user(username):
        user_data = storage.get_user(username)
        if user_data:
            return User(username)
        return None

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            user_data = storage.get_user(username)
            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(username)
                login_user(user)
                return redirect(url_for('dashboard'))
            
            flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if storage.get_user(username):
                flash('Username already exists', 'error')
            else:
                storage.add_user(username, generate_password_hash(password))
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
        
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
