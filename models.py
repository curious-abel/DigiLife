from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    task = db.relationship('Task', backref='task', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def get_password(self, password):
        return check_password_hash(self.password, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(300), nullable=False)
    task_date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.ForeignKey('user.id')) #means this table refers to another another table(User)
    percentage_done=db.Column(db.Integer, default=0)
    note = db.relationship('Note', backref='note') #means the table is referenced somewhere(Note)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    note_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Boolean(), default=False)
    task_id = db.Column(db.ForeignKey('task.id'))

class Jote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content  = db.Column(db.Text)
    date_jotted = db.Column(db.DateTime, default=datetime.now)
    title = db.Column(db.String(150))
    user_id = db.Column(db.ForeignKey('user.id'))

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), default='')
    exp_date = db.Column(db.DateTime)
    color = db.Column(db.String(15), default='#000000')
    user_id = db.Column(db.ForeignKey('user.id'))