from .talky import app
from .schema import db
from . import login
from . import interface

__all__ = [
    'app', 'db', 'login'
]


interface.create_interface(app, login.security)
