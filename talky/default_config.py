import os
from os.path import dirname, join

# Create directory for file fields to use
CLEANUP_FILES = False
FILE_PATH = join(dirname(__file__), 'files')
try:
    os.mkdir(FILE_PATH)
except OSError:
    pass

# The domain talky is hosted at
TALKY_DOMAIN = 'http://localhost:5000'

# Create secret key so we can use sessions
SECRET_KEY = 'CHANGE_ME'

# Limit uploads to 16MB
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Create in-memory database
DATABASE_FILE = 'sample_db.sqlite'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_FILE
SQLALCHEMY_ECHO = False

# Flask-Mail config
MAIL_SERVER = 'CHANGE_ME'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'CHANGE_ME'
MAIL_PASSWORD = 'CHANGE_ME'
MAIL_DEFAULT_SENDER = ('CHANGE_ME', 'CHANGE_ME')

# Flask-Security config
SECURITY_URL_PREFIX = "/secure"
SECURITY_PASSWORD_HASH = "bcrypt"
SECURITY_PASSWORD_SALT = "CHANGE_ME"

# Flask-Security URLs, overridden because they don't put a / at the end
SECURITY_LOGIN_URL = "/login/"
SECURITY_LOGOUT_URL = "/logout/"
# SECURITY_REGISTER_URL = "/register/"
SECURITY_UNAUTHORIZED_VIEW = SECURITY_LOGIN_URL

SECURITY_POST_LOGIN_VIEW = "/secure/user/"
SECURITY_POST_LOGOUT_VIEW = "/secure/login/"
SECURITY_POST_REGISTER_VIEW = "/secure/user/"

# Flask-Security features
SECURITY_CONFIRMABLE = False
SECURITY_REGISTERABLE = False
SECURITY_RECOVERABLE = False
SECURITY_SEND_REGISTER_EMAIL = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

# As I'm paranoid avoid leaking valid user accounts
SECURITY_MSG_USER_DOES_NOT_EXIST = ('Invalid username/password combination', 'error')
SECURITY_MSG_INVALID_PASSWORD = SECURITY_MSG_USER_DOES_NOT_EXIST
