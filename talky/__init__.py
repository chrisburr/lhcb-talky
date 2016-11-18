from flask import Flask

# CONSTANTS CHANGE ME!!!
SECRET_KEY = 'super secret string'
DATABASE_PATH = 'sqlite:////Users/cburr/Desktop/lhcb-belle-coms/talky.db'

# create the application object
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_PATH

from . import login  # NOQA
from . import talk  # NOQA
from . import admin  # NOQA
