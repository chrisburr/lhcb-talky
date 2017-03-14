# [SublimeLinter flake8-max-line-length:120]
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import foreign, remote
from flask_security import UserMixin, RoleMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

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

categories_contacts = db.Table(
    'categories_contacts',
    db.Column('contact_id', db.Integer(), db.ForeignKey('contact.id')),
    db.Column('category_id', db.Integer(), db.ForeignKey('category.id'))
)

interesting_talks_experiment = db.Table(
    'interesting_talks_experiment',
    db.Column('experiment_id', db.Integer(), db.ForeignKey('experiment.id')),
    db.Column('talk_id', db.Integer(), db.ForeignKey('talk.id')),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean(), nullable=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users'))

    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship('Experiment', backref=db.backref('users'))

    def __str__(self):
        return self.email


class Experiment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __str__(self):
        return self.name


class Conference(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000))
    venue = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)

    def __str__(self):
        return self.name


class Comment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    comment = db.Column(db.String(100000), nullable=False)
    time = db.Column(db.DateTime(), nullable=False)

    talk_id = db.Column(db.Integer, db.ForeignKey('talk.id'), nullable=False)
    talk = db.relationship('Talk', backref=db.backref('comments'))

    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=True)
    submission = db.relationship('Submission', backref=db.backref('comments'))

    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    def __str__(self):
        return 'TODO'


class Submission(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    time = db.Column(db.DateTime())
    talk_id = db.Column(db.Integer, db.ForeignKey('talk.id'), nullable=False)
    talk = db.relationship('Talk', backref=db.backref('submissions'))

    def __str__(self):
        return 'TODO'


class Category(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), nullable=False)

    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship('Experiment', backref=db.backref('categories'))

    contacts = db.relationship(
        'Contact', secondary=categories_contacts,
        backref=db.backref('categories')
    )

    def __str__(self):
        return self.name


class Talk(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    abstract = db.Column(db.String(10000))
    duration = db.Column(db.String(80), nullable=False)
    speaker = db.Column(db.String(200), nullable=False)

    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship('Experiment', backref=db.backref('talks'))

    conference_id = db.Column(db.Integer, db.ForeignKey('conference.id'), nullable=False)
    conference = db.relationship('Conference', backref=db.backref('talks'))

    @hybrid_property
    def conference_date(self):
        return self.conference.start_date

    interesting_to = db.relationship(
        'Experiment', secondary=interesting_talks_experiment,
        backref=db.backref('interesting_talks')
    )

    def __str__(self):
        return f'{self.title} - {self.conference.name}'


class Contact(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(200), nullable=False)

    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship('Experiment', backref=db.backref('contacts'))

    def __str__(self):
        return self.email
