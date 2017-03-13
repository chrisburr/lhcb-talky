from flask import Flask, render_template
from flask_mail import Mail

from . import default_config

__all__ = ['app', 'mail']

app = Flask(__name__)
app.config.from_object(default_config)
mail = Mail(app)


@app.route('/')
def index():
    return render_template('index.html')
