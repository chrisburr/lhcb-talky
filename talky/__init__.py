import logging

import colorlog

from .talky import app, mail
from .schema import db
from . import login
from . import interface
from . import database_events

__all__ = [
    'app', 'mail', 'db', 'login', 'database_events'
]

# Setup colourful logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(name)s:%(message)s'
))
handler.setLevel(logging.INFO)

logger = colorlog.getLogger()
logger.addHandler(handler)


interface.create_interface(app, login.security)
