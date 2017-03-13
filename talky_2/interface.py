from flask import url_for, redirect, request, abort
from flask_security import current_user
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers

from . import schema


def _make_filter(table):
    def filter_by_experiment():
        return table.query.filter_by(
            experiment=current_user.experiment
        ).all()
    return filter_by_experiment


class MyBaseView(sqla.ModelView):
    def __init__(self, table=None, session=None):
        table = table or self._table_class
        session = session or schema.db.session
        return super(MyBaseView, self).__init__(table, session)

    def is_accessible(self):
        raise NotImplementedError()

    def _handle_view(self, name, **kwargs):
        # Redirect users when a view is not accessible
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login', next=request.url))

    @property
    def form_columns(self):
        return self.column_list

    def __unicode__(self):
        return self.name


class AdminView(MyBaseView):
    def __init__(self, *args, **kwargs):
        assert 'endpoint' not in kwargs
        super(AdminView, self).__init__(*args, **kwargs)
        self.url = self.endpoint
        self.endpoint = self.endpoint+'_admin'

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        return current_user.has_role('superuser')

    @property
    def column_list(self):
        if hasattr(self, '_column_list'):
            return list(self._column_list)
        else:
            return None


class UserView(MyBaseView):
    def __init__(self, *args, **kwargs):
        assert 'endpoint' not in kwargs
        super(UserView, self).__init__(*args, **kwargs)
        self.url = self.endpoint
        self.endpoint = self.endpoint+'_user'

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        return current_user.has_role('user')

    @property
    def column_list(self):
        columns = list(self._column_list)
        if 'experiment' in self._column_list:
            columns.pop(columns.index('experiment'))
        return columns

    def get_query(self):
        # Limit this view to only the current user's experiment
        return self.session.query(self.model).filter(
            self.model.experiment == current_user.experiment)

    def get_count_query(self):
        # Limit this view to only the current user's experiment
        return self.session.query(sqla.view.func.count('*')).filter(
            self.model.experiment == current_user.experiment)

    def create_form(self):
        form = super(UserView, self).create_form()
        for s in self._add_experiment_filter:
            getattr(form, s).query_factory = _make_filter(self._table_class)
        return form

    def edit_form(self, obj):
        form = super(UserView, self).edit_form(obj)
        for s in self._add_experiment_filter:
            getattr(form, s).query_factory = _make_filter(self._table_class)
        return form

    def on_model_change(self, form, model, is_created):
        model.experiment = current_user.experiment
        super(UserView, self).on_model_change(form, model, is_created)


class DBCategoryView(object):
    _table_class = schema.Category
    _column_list = ('name', 'contacts', 'experiment')
    _form_columns = ('name', 'contacts', 'experiment')
    _add_experiment_filter = ('contacts',)


class DBContactView(object):
    _table_class = schema.Contact
    _column_list = ('email', 'categories', 'experiment')
    _form_columns = ('email', 'categories', 'experiment')
    _add_experiment_filter = ('categories',)


def make_view(user_view, view=None, db=None):
    if view is None and db is not None:
        class CustomView(user_view):
            _table_class = db
    elif view is not None and db is None:
        class CustomView(view, user_view):
            pass
    else:
        raise ValueError()

    return CustomView()


def create_interface(app, security):
    user = flask_admin.Admin(
        app,
        'Talky',
        base_template='my_master.html',
        template_mode='bootstrap3',
        url='/secure/user',
        endpoint='user'
    )

    user.add_view(make_view(UserView, view=DBCategoryView))
    user.add_view(make_view(UserView, view=DBContactView))

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
    admin.add_view(make_view(AdminView, db=schema.Conference))
    admin.add_view(make_view(AdminView, db=schema.Talk))
    admin.add_view(make_view(AdminView, db=schema.Submission))
    admin.add_view(make_view(AdminView, db=schema.Comment))

    # admin.add_view(AdminView(
    #     schema.Role, schema.db.session
    # ))

    # admin.add_view(AdminView(
    #     schema.Experiment, schema.db.session
    # ))

    # admin.add_view(AdminView(
    #     schema.User, schema.db.session
    # ))

    # admin.add_view(UserView(
    #     schema.Contact, schema.db.session
    # ))

    # admin.add_view(UserView(
    #     schema.Conference, schema.db.session
    # ))

    # admin.add_view(UserView(
    #     schema.Talk, schema.db.session
    # ))

    # admin.add_view(AdminView(
    #     schema.Submission, schema.db.session
    # ))

    # admin.add_view(AdminView(
    #     schema.Comment, schema.db.session
    # ))

    @security.context_processor
    def security_context_processor_user():
        return dict(
            admin_base_template=user.base_template,
            admin_view=user.index_view,
            h=admin_helpers,
            get_url=url_for
        )

    # @security.context_processor
    # def security_context_processor_admin():
    #     return dict(
    #         admin_base_template=admin.base_template,
    #         admin_view=admin.index_view,
    #         h=admin_helpers,
    #         get_url=url_for
    #     )
