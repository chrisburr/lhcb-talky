import math

import flask_admin
from flask_admin.contrib import sqla

from .. import schema


class UserHomeView(sqla.ModelView):
    # Permissions
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    can_export = True

    # Templates
    list_template = 'admin/model/list.html'
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
    column_details_list = ['conference_date', 'conference', 'title', 'experiment', 'duration', 'speaker', 'abstract']
    column_details_exclude_list = None
    column_export_exclude_list = None
    column_formatters = {
        'conference_date': lambda v, c, m, n: str(m.conference_date.date())
    }
    column_export_list = ['conference_date', 'conference', 'title', 'experiment', 'duration', 'speaker', 'abstract']
    column_formatters_export = None
    column_type_formatters_export = None
    column_descriptions = None
    column_default_sort = ('conference.start_date', True)
    column_editable_list = None
    column_choices = None
    column_filters = ['title', 'experiment', 'conference', 'title', 'abstract', 'duration', 'speaker']
    named_filter_urls = False
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

    # @flask_admin.expose('/')
    # @flask_admin.expose('/flagged')
    # def index(self):
    #     return self._display('flagged')

    # @flask_admin.expose('/given')
    # def given(self):
    #     return self._display('given')

    # @flask_admin.expose('/other')
    # def other(self):
    #     return self._display('other')
