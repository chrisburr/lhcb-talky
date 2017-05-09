import colorlog

from .talky import app
from .schema import db
from . import login
from . import interface

__all__ = [
    'app', 'db', 'login'
]

# Setup colourful logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(name)s:%(message)s'
))

logger = colorlog.getLogger()
logger.addHandler(handler)


interface.create_interface(app, login.security)
