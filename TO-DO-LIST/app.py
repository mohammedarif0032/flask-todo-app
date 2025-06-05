from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('todo'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('register'))

        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('todo'))
        flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/todo')
def todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify({'tasks': []})
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify({'tasks': [task.content for task in tasks]})

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'})
    content = request.json.get('task')
    if content:
        task = Task(content=content, user_id=session['user_id'])
        db.session.add(task)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})

@app.route('/delete', methods=['POST'])
def delete_task():
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'})
    content = request.json.get('task')
    task = Task.query.filter_by(content=content, user_id=session['user_id']).first()
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'not found'})

if __name__ == '__main__':
    if not os.path.exists('todo.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
