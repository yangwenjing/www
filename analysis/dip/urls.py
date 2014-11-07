from django.conf.urls import patterns, url

urlpatterns = patterns(
    'analysis.dip.views',
    url(r'^jobs/$', 'manage_jobs', name='manage_jobs'),

    url(r'^jobs/create$', 'create_job', name='create_job'),
    url(r'^jobs/(\d+)/edit$', 'create_job', name='edit_job'),
    url(r'^jobs/(\d+)/delete$', 'delete_job', name='delete_job'),

    url(r'^jobs/history$', 'import_history', name='import_history'),
    url(r'^jobs/import$', 'import_job', name='import_job'),
    url(r'^jobs/reimport$', 'reimport_job', name='reimport_job'),
)
