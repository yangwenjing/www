from django.conf.urls import patterns, url

urlpatterns = patterns(
    'analysis.collection.views',
    url(r'^star$', 'star_report', name='star_report'),
    url(r'^list$', 'list_collection', name='list_collection'),
    url(r'^create$', 'create_collection', name='create_collection'),
    url(r'^create/(\d+)$', 'create_collection', name='edit_collection'),
    url(r'^create/report$', 'create_report', name='create_report'),
    url(r'^delete/(\d+)$', 'delete_collection', name='delete_collection'),
    url(r'^feature/(\d+)$', 'feature_collection', name='feature_collection'),
    url(r'^detail/(\d+)$', 'show_collection_detail', name='collection_detail'),

    url(r'^widget/report/change_size$', 'change_report_size', name='change_report_size'),

    url(r'^(\d+)$', 'collection_report', name='collection_report'),

    url(r'^(\d+)/sort$', 'sort_widgets', name='sort_widgets'),
    url(r'^widget/(\d+)/remove$', 'remove_widget', name='remove_widget'),
    url(r'link$', 'list_external_links', name='list_external_links'),
    url(r'link/create$', 'create_link', name='create_links'),
    url(r'link/edit/(\d+)$', 'create_link', name='edit_link'),
    url(r'link/(\d+)$', 'show_link', name='show_link'),
    url(r'link/delete/(\d+)$', 'delete_link', name='delete_link'),
    url(r'collection/group/(\d+)', 'list_collection_link_for_group', name='list_group_collections')
)
