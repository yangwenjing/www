from django.conf.urls import patterns, url

urlpatterns = patterns(
    'analysis.core.views',
    url(r'^database/$', 'manage_databases', name='databases'),
    url(r'^database/create$', 'create_database', name='create_database'),
    url(r'^database/(\d+)/edit$', 'create_database', name='edit_database'),
    url(r'^database/(\d+)/delete$', 'delete_database', name='delete_database'),
    url(r'^database/(\d+)/group$', 'manage_database_group', name='manage_database_group'),

    url(r'^views/$', 'manage_views', name='views'),
    url(r'^views/create$', 'create_report', name='create_view'),
    url(r'^views/(\d+)/edit$', 'create_report', name='edit_view'),
    url(r'^views/(\d+)/delete$', 'delete_view', name='delete_view'),

    url(r'^database/tables$', 'list_tables', name='query_tables'),
    url(r'^database/db_groups/$', 'list_database_groups', name='query_db_groups'),


    url(r'^database/get_sample_data$', 'show_sample_data', name='get_sample_data'),
)
