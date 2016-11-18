import base64
import datetime
import os

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from . import app


db = SQLAlchemy(app)


tags = db.Table(
    'tags',
    db.Column('experiment_id', db.Integer, db.ForeignKey('experiment.id')),
    db.Column('talk_id', db.Integer, db.ForeignKey('talk.id'))
)


class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    tagged = db.relationship("Talk", secondary=tags)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Experiment {0}>'.format(self.name)


class User(UserMixin, db.Model):
    email = db.Column(db.String(80), primary_key=True, unique=True)
    password = db.Column(db.String(120))
    experiment_id = db.Column(db.String(80), db.ForeignKey('experiment.id'))
    experiment = db.relationship('Experiment', backref=db.backref('users', lazy='dynamic'))

    def __init__(self, experiment, email, password):
        self.experiment = Experiment.query.filter_by(name=experiment).first()
        self.email = email
        self.password = password

    def get_id(self):
        return self.email

    def __repr__(self):
        return '<User {0} {1}>'.format(self.email, self.experiment)


class Talk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    abstract = db.Column(db.String(10000))
    experiment_id = db.Column(db.String(80), db.ForeignKey('experiment.id'))
    experiment = db.relationship('Experiment', backref=db.backref('talks', lazy='dynamic'))
    speaker = db.Column(db.String(200))
    talk_date = db.Column(db.String(50))
    view_key = db.Column(db.String(64))
    submit_key = db.Column(db.String(64))

    def __init__(self, title, abstract, experiment, speaker, talk_date, tagged):
        self.title = title
        self.abstract = abstract
        self.speaker = speaker
        self.experiment = Experiment.query.filter_by(name=experiment).first()
        self.talk_date = talk_date
        self.view_key = base64.urlsafe_b64encode(os.urandom(48)).decode('utf-8')
        self.submit_key = base64.urlsafe_b64encode(os.urandom(48)).decode('utf-8')

        for ex in tagged:
            ex = Experiment.query.filter_by(name=ex)
            ex.first().tagged.append(self)

    def __repr__(self):
        return '<Talk {0}>'.format(self.title)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    talk_id = db.Column(db.Integer, db.ForeignKey('talk.id'))
    talk = db.relationship('Talk', backref=db.backref('submissions', lazy='dynamic'))
    submission_date = db.Column(db.String(50))

    def __init__(self, talk):
        self.talk = talk
        self.submission_time = datetime.datetime.utcnow().isoformat()

    def __repr__(self):
        return '<Submission {0} {1}>'.format(self.talk, self.submission_time)
