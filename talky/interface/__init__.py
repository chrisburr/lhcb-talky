from flask import url_for
import flask_admin
from flask_admin import helpers as admin_helpers

from .. import schema

from .views import make_view, UserView, AdminView
from .views import DBCategoryView, DBContactView, DBConferenceView, DBTalkView
from .home import UserHomeView


def create_interface(app, security):
    user = flask_admin.Admin(
        app,
        'Talky',
        base_template='my_master.html',
        template_mode='bootstrap3',
        url='/secure/user',
        endpoint='user',
        index_view=UserHomeView(name='Talks', url='/secure/user', endpoint='home')
    )

    user.add_view(make_view(UserView, view=DBCategoryView))
    user.add_view(make_view(UserView, view=DBContactView))
    user.add_view(make_view(UserView, view=DBConferenceView))

    admin = flask_admin.Admin(
        app,
        'Talky - Admin',
        base_template='my_master.html',
        template_mode='bootstrap3',
        url='/secure/admin',
        endpoint='admin'
    )

    admin.add_view(make_view(AdminView, db=schema.Role))
    admin.add_view(make_view(AdminView, db=schema.Experiment))
    admin.add_view(make_view(AdminView, db=schema.User))
    admin.add_view(make_view(AdminView, view=DBContactView))
    admin.add_view(make_view(AdminView, view=DBCategoryView))
    admin.add_view(make_view(AdminView, view=DBConferenceView))
    admin.add_view(make_view(AdminView, view=DBTalkView))
    admin.add_view(make_view(AdminView, db=schema.Submission))
    admin.add_view(make_view(AdminView, db=schema.Comment))

    @security.context_processor
    def security_context_processor_user():
        return dict(
            admin_base_template=user.base_template,
            admin_view=user.index_view,
            h=admin_helpers,
            get_url=url_for
        )
