from django.conf.urls import patterns, url

urlpatterns = patterns(
    'analysis.aggregate.views',
    url(r'^create$', 'create_aggregation', name='create_aggregation'),
    url(r'^edit/(\d+)$', 'create_aggregation', name='edit_aggregation'),
    url(r'^delete/(\d+)$', 'delete_aggregation', name='delete_aggregation'),
    url(r'^history$', 'aggregate_history', name='aggregate_history'),
    url(r'^list$', 'list_aggregate_job', name='aggregate_list'),

)
