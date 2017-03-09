from flask import url_for, redirect, render_template, request, abort
from flask_security import Security, SQLAlchemyUserDatastore, current_user
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers

from .talky import app
from . import schema


user_datastore = SQLAlchemyUserDatastore(schema.db, schema.User, schema.Role)
security = Security(app, user_datastore)


# Create customized model view class
class MyModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


# Flask views
@app.route('/')
def index():
    return render_template('index.html')


# Create admin
admin = flask_admin.Admin(
    app,
    'Example: Auth',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(MyModelView(schema.Role, schema.db.session))
admin.add_view(MyModelView(schema.User, schema.db.session))
admin.add_view(MyModelView(schema.Experiment, schema.db.session))
admin.add_view(MyModelView(schema.Conference, schema.db.session))
admin.add_view(MyModelView(schema.Comment, schema.db.session))
admin.add_view(MyModelView(schema.Submission, schema.db.session))
admin.add_view(MyModelView(schema.Category, schema.db.session))
admin.add_view(MyModelView(schema.Talk, schema.db.session))
admin.add_view(MyModelView(schema.Contact, schema.db.session))


# Define a context processor for merging flask-admin's template context into
# the flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )
