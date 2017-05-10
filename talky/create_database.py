# [SublimeLinter flake8-max-line-length:120]
from datetime import datetime, timedelta
import random
import os
from os.path import join, isdir

from matplotlib import pyplot as plt
from flask_security.utils import encrypt_password
import lipsum

from .talky import app
from .login import user_datastore
from .schema import db, Role, Experiment, Conference, Comment, Submission, Category, Talk, Contact


__all__ = [
    'build_sample_db'
]


def get_delta(days=2):
    return timedelta(
        days=random.randrange(days),
        hours=random.randrange(24),
        minutes=random.randrange(60),
        seconds=random.randrange(60)
    )


def make_example_submission(talk, version):
    plt.title(talk.title)
    plt.text(0.1, 0.5, talk.experiment.name)
    submission_dir = join(app.config['FILE_PATH'], str(talk.id), str(version))
    assert not isdir(submission_dir)
    os.makedirs(submission_dir)
    plt.savefig(join(submission_dir, 'my_example_file.pdf'))
    plt.close()


def make_submissions(first_names, conference, talk):
    submissions = []
    current_time = conference.start_date
    for n_submission in range(random.randrange(5)):
        talk.n_submissions += 1
        version = talk.n_submissions
        make_example_submission(talk, version)
        current_time = current_time + get_delta()
        submission = Submission(talk=talk, time=current_time, version=version, filename='my_example_file.pdf')
        db.session.add(submission)
        submissions.append(submission)

    current_time = conference.start_date
    for n_comment in range(random.randrange(1, 6)):
        make_comment(first_names, current_time, talk, submissions, parent=None)


def make_comment(first_names, current_time, talk, submissions, parent=None, child_prob=0.75):
    current_time = current_time + get_delta(3)
    name = random.sample(first_names, 2)
    s = [s for s in submissions if s.time < current_time]
    comment = Comment(
        name=' '.join(name),
        email=f'{name[0]}.{name[1]}@cern.ch',
        comment=lipsum.generate_sentences(random.randrange(1, 5)),
        time=current_time,
        talk=talk,
        submission=s[-1] if s else None,
        parent_comment_id=parent
    )
    db.session.add(comment)
    db.session.commit()

    if random.random() > 1-child_prob:
        for n_comment in range(random.randrange(1, 4)):
            make_comment(first_names, current_time, talk, submissions, comment.id, child_prob*0.5)


def build_sample_db(fast=False):
    """Populate a db with some example entries."""

    db.drop_all()
    db.create_all()

    with app.app_context():
        lhcb = Experiment(name='LHCb')
        belle = Experiment(name='Belle')
        belle_2 = Experiment(name='Belle 2')
        db.session.add(lhcb)
        db.session.add(belle)
        db.session.add(belle_2)
        db.session.commit()

        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        test_admin = user_datastore.create_user(
            name='Admin',
            email='admin',
            password=encrypt_password('admin'),
            roles=[user_role, super_user_role],
            experiment=lhcb
        )
        test_user_lhcb = user_datastore.create_user(
            name='User',
            email='userlhcb',
            password=encrypt_password('user'),
            roles=[user_role],
            experiment=lhcb
        )
        test_user_belle = user_datastore.create_user(
            name='User',
            email='userbelle',
            password=encrypt_password('user'),
            roles=[user_role],
            experiment=belle
        )
        test_user_belle2 = user_datastore.create_user(
            name='User',
            email='userbelle2',
            password=encrypt_password('user'),
            roles=[user_role],
            experiment=belle_2
        )

        first_names = [
            'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
            'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
            'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        ]

        contacts = []
        for i in range(6 if fast else len(first_names)):
            tmp_experiment = [lhcb, belle, belle_2][i % 3]
            tmp_email = f'{first_names[i].lower()}@{tmp_experiment.name}.com'
            contacts.append(Contact(email=tmp_email, experiment=tmp_experiment))
            db.session.add(contacts[-1])
        db.session.commit()

        lhcb_charm = Category(name='Charm', experiment=lhcb, contacts=contacts[:1])
        belle_charm = Category(name='Charm', experiment=belle, contacts=contacts[1:2])
        db.session.add(lhcb_charm)
        db.session.add(belle_charm)
        db.session.commit()

        conferences = []
        for year in range(2019 if fast else 2000, 2020):
            conf_time = datetime.now() - timedelta(days=random.randrange(50, 500))
            llwi = Conference(name='LLWI '+str(year), venue='Canada', start_date=conf_time)
            db.session.add(llwi)
            conf_time = datetime.now() - timedelta(days=random.randrange(50, 500))
            morriond = Conference(name='Moriond '+str(year), venue='La Thuile', start_date=conf_time, url=f'http://moriond.in2p3.fr/QCD/{year}/')
            db.session.add(morriond)
            conferences.extend([llwi, morriond])
        db.session.commit()

        for conference in conferences:
            charm_prod = Talk(
                title='Charm hadron production cross-sections at √s = 13 TeV using 300pb⁻¹', duration=f'{random.randrange(10, 90)}" (+ questions)', speaker=f'{".".join(random.sample(first_names, 2))}@cern.ch',
                experiment=lhcb, interesting_to=[belle, belle_2], conference=conference, abstract=lipsum.generate_sentences(10)
            )
            db.session.add(charm_prod)
            db.session.commit()
            make_submissions(first_names, conference, charm_prod)

            talk = Talk(
                title=lipsum.generate_words(10), duration=f'{random.randrange(10, 90)}"', speaker=f'{".".join(random.sample(first_names, 2))}@cern.ch',
                experiment=belle, interesting_to=[lhcb], conference=conference, abstract=lipsum.generate_paragraphs(2)
            )
            db.session.add(talk)
            db.session.commit()
            make_submissions(first_names, conference, talk)

            talk = Talk(
                title=lipsum.generate_words(10), duration=f'{random.randrange(10, 90)}"', speaker=f'{".".join(random.sample(first_names, 2))}@cern.ch',
                experiment=belle_2, interesting_to=[belle], conference=conference, abstract=lipsum.generate_paragraphs(2)
            )
            db.session.add(talk)
            db.session.commit()
            make_submissions(first_names, conference, talk)

        db.session.commit()
