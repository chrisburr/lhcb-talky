from flask import Flask

from . import default_config

app = Flask(__name__)
app.config.from_object(default_config)
