from math import ceil

from flask.ext.admin.base import expose
from flask_admin.contrib import sqla
from flask_security import current_user
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from flask import request, redirect, flash, url_for
from flask_admin.babel import gettext

from .. import schema


class UserHomeView(sqla.ModelView):
    # Permissions
    can_create = True
    can_edit = False
    can_delete = False
    can_view_details = True
    can_export = True

    # Templates
    list_template = 'home/list.html'
    edit_template = 'admin/model/edit.html'
    create_template = 'admin/model/create.html'
    details_template = 'admin/model/details.html'
    edit_modal_template = 'admin/model/modals/edit.html'
    create_modal_template = 'admin/model/modals/create.html'
    details_modal_template = 'admin/model/modals/details.html'

    # Modals
    edit_modal = False
    create_modal = False
    details_modal = False

    # Customizations
    column_list = ['conference_date', 'conference', 'title', 'experiment', 'duration', 'speaker']
    column_details_list = ['conference_date', 'conference', 'title', 'experiment', 'interesting_to', 'duration', 'speaker', 'abstract']
    column_details_exclude_list = None
    column_export_exclude_list = None
    column_formatters = {
        'conference_date': lambda v, c, m, n: str(m.conference_date.date())
    }
    column_export_list = ['conference_date', 'conference', 'title', 'experiment', 'interesting_to', 'duration', 'speaker', 'abstract']
    column_formatters_export = None
    column_type_formatters_export = None
    column_descriptions = None
    column_default_sort = ('conference.start_date', True)
    column_editable_list = None
    column_choices = None
    column_filters = ['title', 'experiment.name', 'interesting_to.name', 'conference', 'title', 'abstract', 'duration', 'speaker']
    named_filter_urls = True
    column_display_actions = True
    column_extra_row_actions = None
    simple_list_pager = False
    column_sortable_list = [
        ('experiment', 'experiment.name'),
        ('conference_date', 'conference.start_date'),
        ('conference', 'conference.name'),
        'title', 'duration', 'speaker'
    ]
    form = None
    # form_base_class = BaseForm
    form_args = None
    form_columns = None
    form_overrides = None
    form_widget_args = None
    form_extra_fields = None
    form_ajax_refs = None
    form_rules = None

    form_edit_rules = None
    form_create_rules = None

    # Export settings
    export_max_rows = 0
    export_types = ['json', 'xlsx', 'yaml', 'csv']

    # Pagination settings
    page_size = 20
    can_set_page_size = True

    def __init__(self, name=None, category=None, endpoint=None, url=None,
                 static_folder=None, menu_class_name=None, menu_icon_type=None,
                 menu_icon_value=None):
        super(UserHomeView, self).__init__(
            schema.Talk, schema.db.session, name, category, endpoint, url,
            static_folder, menu_class_name, menu_icon_type, menu_icon_value
        )

    def is_accessible(self):
        # Restrict access to active users
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        return current_user.has_role('user')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))

    @expose('/details/')
    def details_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_view_details:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        talk = self.get_one(id)

        if talk is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        return redirect(f'/view/{talk.id}/{talk.view_key}')

    def _get_list_url(self, view_args):
        """
            Generate page URL with current page, sort column and
            other parameters.
            :param view:
                View name
            :param view_args:
                ViewArgs object with page number, filters, etc.
        """
        page = view_args.page or None
        desc = 1 if view_args.sort_desc else None

        kwargs = dict(page=page, sort=view_args.sort, desc=desc, search=view_args.search)
        kwargs.update(view_args.extra_args)

        if view_args.page_size:
            kwargs['page_size'] = view_args.page_size

        kwargs.update(self._get_filters(view_args.filters))

        view_type = view_args.extra_args['view_type']
        del kwargs['view_type']

        if view_type == 'all':
            return self.get_url('.all_view', **kwargs)
        elif view_type == 'flagged':
            return self.get_url('.index_view', **kwargs)
        elif view_type == 'given':
            return self.get_url('.given_view', **kwargs)
        elif view_type == 'other':
            return self.get_url('.other_view', **kwargs)
        else:
            raise RuntimeError(view_type)

    # Views
    def _show_list_view(self, view_type):
        """
            List view
        """
        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Grab parameters from URL
        view_args = self._get_list_extra_args()
        view_args.extra_args = {'view_type': view_type}

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get page size
        page_size = view_args.page_size or self.page_size

        filters = list(view_args.filters)
        if view_type == 'given':
            idx, _filter = self._filter_args['experiment_experiment_name_equals']
            filters.insert(0, (idx, None, current_user.experiment.name))
        elif view_type == 'flagged':
            idx, _filter = self._filter_args['interestingto_experiment_name_equals']
            filters.insert(0, (idx, None, current_user.experiment.name))
        elif view_type == 'other':
            idx, _filter = self._filter_args['experiment_experiment_name_not_equal']
            filters.insert(0, (idx, None, current_user.experiment.name))
            idx, _filter = self._filter_args['interestingto_experiment_name_not_in_list']
            filters.insert(0, (idx, None, current_user.experiment.name))
        elif view_type == 'all':
            pass
        else:
            raise RuntimeError(view_type)
        print('*'*100, view_args.filters)
        print(view_args)

        # Get count and data
        count, data = self.get_list(view_args.page, sort_column, view_args.sort_desc,
                                    view_args.search, filters, page_size=page_size)

        list_forms = {}
        if self.column_editable_list:
            for row in data:
                list_forms[self.get_pk_value(row)] = self.list_form(obj=row)

        # Calculate number of pages
        if count is not None and page_size:
            num_pages = int(ceil(count / float(page_size)))
        elif not page_size:
            num_pages = 0  # hide pager for unlimited page_size
        else:
            num_pages = None  # use simple pager

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_list_url(view_args.clone(page=p))

        def sort_url(column, invert=False, desc=None):
            if not desc and invert and not view_args.sort_desc:
                desc = 1

            return self._get_list_url(view_args.clone(sort=column, sort_desc=desc))

        def page_size_url(s):
            if not s:
                s = self.page_size

            return self._get_list_url(view_args.clone(page_size=s))

        # Actions
        actions, actions_confirmation = self.get_actions_list()
        if actions:
            action_form = self.action_form()
        else:
            action_form = None

        clear_search_url = self._get_list_url(view_args.clone(page=0,
                                                              sort=view_args.sort,
                                                              sort_desc=view_args.sort_desc,
                                                              search=None,
                                                              filters=None))

        return self.render(
            self.list_template,
            view_type=view_type,
            data=data,
            list_forms=list_forms,
            delete_form=delete_form,
            action_form=action_form,

            # List
            list_columns=self._list_columns,
            sortable_columns=self._sortable_columns,
            editable_columns=self.column_editable_list,
            list_row_actions=self.get_list_row_actions(),

            # Pagination
            count=count,
            pager_url=pager_url,
            num_pages=num_pages,
            can_set_page_size=self.can_set_page_size,
            page_size_url=page_size_url,
            page=view_args.page,
            page_size=page_size,
            default_page_size=self.page_size,

            # Sorting
            sort_column=view_args.sort,
            sort_desc=view_args.sort_desc,
            sort_url=sort_url,

            # Search
            search_supported=self._search_supported,
            clear_search_url=clear_search_url,
            search=view_args.search,

            # Filters
            filters=self._filters,
            filter_groups=self._get_filter_groups(),
            active_filters=view_args.filters,
            filter_args=self._get_filters(view_args.filters),

            # Actions
            actions=actions,
            actions_confirmation=actions_confirmation,

            # Misc
            enumerate=enumerate,
            get_pk_value=self.get_pk_value,
            get_value=self.get_list_value,
            return_url=self._get_list_url(view_args),
        )

    @expose('/all')
    def all_view(self):
        return self._show_list_view('all')

    @expose('/')
    @expose('/flagged')
    def index_view(self):
        return self._show_list_view('flagged')

    @expose('/given')
    def given_view(self):
        return self._show_list_view('given')

    @expose('/other')
    def other_view(self):
        return self._show_list_view('other')
