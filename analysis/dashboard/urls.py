from django.conf.urls import patterns, url

urlpatterns = patterns(
    'analysis.dashboard.views',
    url(r'^$', 'dashboard', name='dashboard'),

    url(r'^report/$', 'my_reports', name='my_reports'),
    url(r'^report/(\d+)$', 'view_report', name='dashboard_report'),
)
