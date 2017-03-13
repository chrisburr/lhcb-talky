# [SublimeLinter flake8-max-line-length:120]
from datetime import datetime

from flask_security.utils import encrypt_password

from .talky import app
from .login import user_datastore
from .schema import db, Role, Experiment, Conference, Comment, Submission, Category, Talk, Contact


def build_sample_db():
    """
    Populate a small db with some example entries.
    """
    import string
    import random

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

        llwi_2016 = Conference(name='LLWI 2016', venue='Canada', start_date=datetime.now())
        db.session.add(llwi_2016)
        morriond_2016 = Conference(name='Moriond 2016', venue='Corshavall', start_date=datetime.now())
        db.session.add(morriond_2016)
        db.session.commit()

        charm_prod = Talk(
            title='Charm Production', duration='12"', speaker='j.b@cern.ch',
            experiment=lhcb, interesting_to=[belle, belle_2], conference=llwi_2016
        )
        db.session.add(charm_prod)
        ew_prod = Talk(
            title='EW Production', duration='25"', speaker='b.f@cern.ch',
            experiment=belle, interesting_to=[lhcb], conference=morriond_2016
        )
        db.session.add(ew_prod)
        db.session.commit()

    return


if __name__ == '__main__':
    build_sample_db()
