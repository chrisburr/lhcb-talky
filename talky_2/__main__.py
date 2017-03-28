# [SublimeLinter flake8-max-line-length:120]
from datetime import datetime, timedelta
import string
import random

from flask_security.utils import encrypt_password
import lipsum

from .talky import app
from .login import user_datastore
from .schema import db, Role, Experiment, Conference, Comment, Submission, Category, Talk, Contact


def get_delta(days=2):
    return timedelta(
        days=random.randrange(days),
        hours=random.randrange(24),
        minutes=random.randrange(60),
        seconds=random.randrange(60)
    )


def make_submissions(first_names, conference, talk):
    submissions = []
    current_time = conference.start_date
    for n_submission in range(random.randrange(5)):
        current_time = current_time + get_delta()
        submission = Submission(talk=talk, time=current_time)
        db.session.add(submission)
        submissions.append(submission)

    current_time = conference.start_date
    for n_comment in range(random.randrange(5)):
        make_comment(first_names, current_time, talk, submissions, parent=None)


def make_comment(first_names, current_time, talk, submissions, parent=None):
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
    if random.random() > 0.5:
        for n_comment in range(1, random.randrange(3)):
            make_comment(first_names, current_time, talk, submissions, parent=comment.id)


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

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

        first_names = [
            'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
            'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
            'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
        ]

        contacts = []
        for i in range(len(first_names)):
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
        for year in range(2000, 2020):
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

            ew_prod = Talk(
                title=lipsum.generate_words(10), duration=f'{random.randrange(10, 90)}"', speaker=f'{".".join(random.sample(first_names, 2))}@cern.ch',
                experiment=belle, interesting_to=[lhcb], conference=conference, abstract=lipsum.generate_paragraphs(2)
            )
            db.session.add(ew_prod)
            db.session.commit()
            make_submissions(first_names, conference, ew_prod)

        db.session.commit()

    return


if __name__ == '__main__':
    build_sample_db()
