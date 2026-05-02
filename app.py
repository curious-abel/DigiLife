from flask import Flask, redirect, render_template, request, url_for, flash, jsonify, json
from models import db, User, Task, Note, Jote, Reminder
from flask_migrate import Migrate
import os
from datetime import datetime
from flask_login import current_user, login_user, login_required, LoginManager, logout_user


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') #'sqlite:///note.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = app.config['SECRET_KEY'] =  os.environ.get('SECRET_KEY', 'fallback-key')
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    task = current_user.task
    #task = Task.query.filter_by(user_id=current_user.id).all()
    user = current_user
    if request.method=='POST':
        task_name = request.form.get('task_name')
        if not task_name:
            flash('you cannot save empty task', 'muted')
            return redirect(url_for('home'))
        task1 = Task(task_name=task_name, user_id=current_user.id)
        db.session.add(task1)
        db.session.commit()
        new_task = Task.query.filter_by(user_id=current_user.id).order_by(Task.task_date.desc()).first()
        
        return redirect(url_for('note', task_id=new_task.id))
    return render_template('home.html', user=user, task=task)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        username = request.form.get('username')
        email=request.form.get('email')
        password1 = request.form.get('password1')
        password=request.form.get('password2')
        if password1 != password:
            flash('password not matched!', 'danger')
            return redirect(url_for('register'))
      

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('the user already exist, please login', 'muted')
            return redirect(url_for('login'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))  
    return render_template('register.html') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.get_password(password):
            flash('login successful', 'success')
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('wrong login details! try again', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/note/<int:task_id>', methods=['GET', 'POST'])
@login_required
def note(task_id):
    task = Task.query.get_or_404(task_id)
    percentage(task_id=task_id)
    note = Note.query.filter_by(task_id=task_id).all()
    if request.method=='POST':
        content = request.form.get('content')
        if not content:
            flash('please enter your task', 'muted')
            return redirect(url_for('note', task_id=task_id))
        new_note = Note(content=content, task_id=task_id)
        db.session.add(new_note)
        db.session.commit()
        
        return redirect(url_for('note', task_id=task_id))
    return render_template('note.html', note=note, task=task)

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    note = Note.query.get_or_404(id)

    if request.method=='POST':

        completed=request.form.get('completed')
        if completed:
            note.status=True
        else:
            note.status=False
        db.session.add(note)
        db.session.commit()
        
       
        return redirect(url_for('note', task_id=note.task_id))


def percentage(task_id):
    
    all_items = Note.query.filter_by(task_id=task_id).all()
    completed = Note.query.filter_by(task_id=task_id, status=True).all()
    available_task = len(all_items)
    comeplete_task = len(completed)
    if comeplete_task>0:
        
        percentage_done = int((comeplete_task/available_task)*100)
        
    else:
        percentage_done = 0
    task = Task.query.get_or_404(task_id)
    task.percentage_done=percentage_done
    db.session.add(task)
    db.session.commit()
    
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('note', task_id = note.task_id))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    note = Note.query.get_or_404(id)
    if request.method=='POST':
        content = request.form.get('content')
        note.content=content
        db.session.commit()
        return redirect(url_for('note', task_id=note.task_id))
    return render_template('edit.html', note=note)

@app.route('/delete_task/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/edit_task/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    
    if request.method=='POST':
        task_name = request.form.get('task_name')
        if not task_name:
            flash('task name cannot be empty, enter a name', 'danger')
            return redirect(url_for('edit_task', id=task.id))
        task.task_name = task_name
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit_task.html', task=task)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    
    if request.method=='POST':
        old_pwd = request.form.get('old')
        new_pwd = request.form.get('new')
        confirm_new = request.form.get('confirm-new')
        if not current_user.get_password(old_pwd):
            flash('please enter correct current password', 'danger')
            return redirect(url_for('change_password'))
        if new_pwd !=confirm_new:
            flash('new password do not match', 'danger')
            return redirect(url_for('change_password'))
        if current_user.get_password(old_pwd):
            current_user.set_password(new_pwd)
            db.session.commit()
            flash('password changed successfully', 'success')
            return redirect(url_for('login'))
    return render_template('change_password.html')

@app.route('/jotter')
def jotter():
    return render_template('jotter.html')

@app.route('/notes')
def notes():
    notes = Jote.query.order_by(Jote.id.desc()).all()
    return jsonify([{'id': note.id,
                    'title': note.title,
                    'content': note.content} for note in notes])

@app.route('/delete_note/<int:id>', methods=['POST'])
def delete_note(id):
    note = Jote.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'status': 'done'})

@app.route('/create_note', methods=['POST'])
def create_note():
    note = Jote()
    db.session.add(note)
    db.session.commit()
    return jsonify({'id': note.id})

@app.route('/load_note/<int:id>')
def load_note(id):
    note = Jote.query.get_or_404(id)
    return jsonify({'id': note.id, 'title': note.title, 'content': note.content})

@app.route('/save_note/<int:id>', methods=['POST'])
def save(id):
    data = request.json
    note = Jote.query.get_or_404(id)
    capital = data.get('title', '').upper()
    note.title = capital
    note.content = data.get('content', '')
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/diary')
def reminder():
    return render_template('diary.html')
    
@app.route('/events')
def events():
    events = Reminder.query.order_by(Reminder.exp_date).all()
    return jsonify([{'event': event.content, 'time': event.exp_date.strftime("%Y-%m-%d") if event.exp_date else None, 'id': event.id} for event in events])

@app.route('/create', methods=['POST'])
def create():
    print('print something')
    event = Reminder()
    db.session.add(event)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/saving/<int:id>', methods=['POST'])
def saving(id):
    data = request.get_json()
    reminder = Reminder.query.get_or_404(id)
    reminder.content = data.get('reminder')
    date = data.get('date')
    converted_date = datetime.strptime(date, "%Y-%m-%d").date()
    reminder.exp_date = converted_date
    print(reminder.content)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/delEvent/<int:id>', methods=['POST'])
def delete_event(id):
    event = Reminder.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'status': 'done'})

@app.route('/check-users')
@login_required
def check_users():
    user_count = User.query.count()
    return render_template('check_users.html', user_count=user_count)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__=='__main__':
    #with app.app_context():
     #   db.drop_all()
        #db.create_all()
    port = int(os.environ.get("PORT", 10000))  # fallback to 10000 if PORT not set
    app.run(host="0.0.0.0", port=port, debug=False)
    #app.run(debug=True)

