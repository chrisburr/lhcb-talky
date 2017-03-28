from flask import Flask, redirect, url_for
from flask_mail import Mail

from . import default_config

__all__ = ['app', 'mail']

app = Flask(__name__)
app.config.from_object(default_config)
mail = Mail(app)


@app.route('/')
def index():
    return redirect(url_for('security.login'))
