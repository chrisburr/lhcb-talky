from flask import url_for, redirect, request, abort
from flask_security import current_user
import flask_admin
from flask_admin.contrib import sqla

from .. import schema


class BaseView(sqla.ModelView):
    def __init__(self, table=None, session=None, **kwargs):
        table = table or self._table_class
        session = session or schema.db.session
        super(BaseView, self).__init__(table, session, **kwargs)
        if 'url' not in kwargs:
            self.url = self.endpoint
        if 'endpoint' not in kwargs:
            self.endpoint = f'{self.endpoint}_{self._endpoint_suffix}'

    def _handle_view(self, name, **kwargs):
        # Redirect users when a view is not accessible
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login', next=request.url))

    def _make_filter(self, table):
        def filter_by_experiment():
            return table.query.filter_by(
                **{'experiment': current_user.experiment}
            ).all()
        return filter_by_experiment

    def __unicode__(self):
        return self.name


class AdminView(BaseView):
    _endpoint_suffix = 'admin'

    def is_accessible(self):
        # Restrict access to active superusers
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        return current_user.has_role('superuser')

    @property
    def form_columns(self):
        if hasattr(self, '_form_columns'):
            return list(self._form_columns)
        else:
            return None

    @property
    def column_list(self):
        if hasattr(self, '_column_list'):
            return list(self._column_list)
        else:
            return self.form_columns


class UserView(BaseView):
    _endpoint_suffix = 'user'

    def is_accessible(self):
        # Restrict access to active users
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        return current_user.has_role('user')

    @property
    def form_columns(self):
        columns = list(self._form_columns)
        if 'experiment' in self._form_columns:
            columns.pop(columns.index('experiment'))
        return columns

    @property
    def column_list(self):
        if hasattr(self, '_column_list'):
            columns = list(self._column_list)
            if 'experiment' in self._column_list:
                columns.pop(columns.index('experiment'))
            return columns
        else:
            return self.form_columns

    def get_query(self):
        if hasattr(self.model, 'experiment') and self.model != schema.Talk:
            # Limit this view to only the current user's experiment
            return self.session.query(self.model).filter(
                self.model.experiment == current_user.experiment)
        else:
            return super(UserView, self).get_query()

    def get_count_query(self):
        if hasattr(self.model, 'experiment') and self.model != schema.Talk:
            # Limit this view to only the current user's experiment
            return self.session.query(sqla.view.func.count('*')).filter(
                self.model.experiment == current_user.experiment)
        else:
            return super(UserView, self).get_count_query()

    def create_form(self):
        form = super(UserView, self).create_form()
        # Filter any query based fields to limit them to the current experiment
        for name, model in self._add_filter:
            getattr(form, name).query_factory = self._make_filter(model)
        return form

    def edit_form(self, obj):
        form = super(UserView, self).edit_form(obj)
        # Filter any query based fields to limit them to the current experiment
        for name, model in self._add_filter:
            getattr(form, name).query_factory = self._make_filter(model)
        return form

    def on_model_change(self, form, model, is_created):
        # if 'experiment' in self.column_list:
        if hasattr(model, 'experiment'):
            # Set the experiment field if present
            model.experiment = current_user.experiment
        super(UserView, self).on_model_change(form, model, is_created)


class DBCategoryView(object):
    _table_class = schema.Category
    _form_columns = ('name', 'contacts', 'experiment')
    _add_filter = [('contacts', schema.Contact)]


class DBContactView(object):
    _table_class = schema.Contact
    _form_columns = ('email', 'categories', 'experiment')
    _add_filter = [('categories', schema.Category)]


class DBConferenceView(object):
    _table_class = schema.Conference
    _form_columns = ('name', 'venue', 'start_date', 'url')
    # TODO This isn't robust
    _add_filter = []

    @property
    def can_delete(self):
        return isinstance(self, AdminView)


class DBTalkView(object):
    can_view_details = True
    column_details_list = (
        'conference', 'title', 'duration', 'experiment', 'speaker',
        'interesting_to', 'abstract'
    )
    can_export = True
    _table_class = schema.Talk
    _form_columns = (
        'conference', 'title', 'duration', 'experiment', 'speaker',
        'interesting_to', 'abstract'
    )
    _column_list = (
        'conference', 'title', 'duration', 'experiment', 'speaker',
        'interesting_to'
    )
    _add_filter = []

    def _make_filter(self, model):
        def filter_by_experiment():
            return model.query.filter(model.id.isnot(current_user.experiment.id)).all()
        return filter_by_experiment

    def create_form(self):
        try:
            form = super(UserView, self).create_form()
            # Filter any query based fields to limit them to the current experiment
            getattr(form, 'interesting_to').query_factory = self._make_filter(schema.Experiment)
        except TypeError:
            form = super(AdminView, self).create_form()
        return form

    def edit_form(self, obj):
        try:
            form = super(UserView, self).edit_form(obj)
            # Filter any query based fields to limit them to the current experiment
            getattr(form, 'interesting_to').query_factory = self._make_filter(schema.Experiment)
        except TypeError:
            form = super(AdminView, self).create_form()
        return form


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
