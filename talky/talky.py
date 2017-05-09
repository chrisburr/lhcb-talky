from flask import Flask, redirect, url_for
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect

from . import default_config

__all__ = ['app', 'mail', 'csrf']

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.from_object(default_config)
mail = Mail(app)
csrf = CSRFProtect(app)


@app.route('/')
def index():
    return redirect(url_for('security.login'))

# msg = Message('Started application')
# msg.recipients = ['chrisburr73@gmail.com']
# msg.body = 'testing'
# mail.send(msg)
