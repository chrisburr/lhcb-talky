from flask_security import Security, SQLAlchemyUserDatastore
from .talky import app
from . import schema


user_datastore = SQLAlchemyUserDatastore(schema.db, schema.User, schema.Role)
security = Security(app, user_datastore)
