from talky.data import db, User, Experiment, Talk

db.drop_all()
db.create_all()

# Experiments
experiments = [
    Experiment('LHCb'),
    Experiment('Belle 2'),
    Experiment('IceCube'),
]

for experiment in experiments:
    db.session.add(experiment)
db.session.commit()

# Users
users = [
    User('LHCb', 'c.b@cern.ch', 'password'),
    User('LHCb', 'marco@cern.ch', 'password'),
]

for user in users:
    db.session.add(user)
db.session.commit()

# Talks
talks = [
    Talk('Searching for D->hll',
         'In this talk we will',
         'LHCb',
         'christopher.burr@cern.ch',
         '2016-11-17T00:00:00.000000',
         ['Belle 2', 'IceCube']),
    Talk('CP violation in Lc decays',
         'In this talk we will',
         'LHCb',
         'alex.pearce@cern.ch',
         '2016-11-17T00:00:00.000000',
         ['Belle 2']),
    Talk('CP violation in Lc decays',
         'In this talk we will',
         'Belle 2',
         'james.smith@other.org',
         '2016-11-17T00:00:00.000000',
         ['LHCb']),
    Talk('PeV scale neutrino events in IceCube',
         'In this talk we will',
         'IceCube',
         'john.snow@hbo.com',
         '2016-11-17T00:00:00.000000',
         [])
]

for talk in talks:
    db.session.add(talk)
db.session.commit()
