from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

from .talky import app

__all__ = [
    'db', 'Role', 'User', 'Experiment', 'Conference', 'Comment', 'Submission',
    'Category', 'Talk', 'Contact'
]


db = SQLAlchemy(app)

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


class Experiment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __str__(self):
        return self.name


class Conference(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(200))
    url = db.Column(db.String(1000))
    venue = db.Column(db.String(200))
    start_date = db.Column(db.DateTime())

    def __str__(self):
        return ''


class Comment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.String(80)
    email = db.Column(db.String(200))
    comment = db.Column(db.String(100000))
    time = db.Column(db.DateTime())

    def __str__(self):
        return ''


class Submission(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    time = db.Column(db.DateTime())

    def __str__(self):
        return ''


class Category(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __str__(self):
        return ''


class Talk(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(200), unique=True)
    abstract = db.Column(db.String(10000), unique=True)
    duration = db.Column(db.String(80), unique=True)
    speaker = db.Column(db.String(200))

    def __str__(self):
        return ''


class Contact(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(200))

    def __str__(self):
        return ''
