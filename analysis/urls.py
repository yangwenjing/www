from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'analysis.dashboard.views.home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('analysis.account.urls')),

    url(r'^dashboard/collection/', include('analysis.collection.urls')),
    url(r'^dashboard/', include('analysis.dashboard.urls')),

    url(r'^manage/', include('analysis.dip.urls')),
    url(r'^manage/aggregate/', include('analysis.aggregate.urls')),
    url(r'^manage/', include('analysis.core.urls')),
)
