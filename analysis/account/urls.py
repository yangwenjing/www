from django.conf.urls import patterns, url

urlpatterns = patterns(
    'analysis.account.views',
    url(r'^login/', 'login_view', name='account_login'),
    url(r'^logout$', 'logout_view', name='account_logout'),
    url(r'^users$', 'manage_users_view', name='users'),
    url(r'^group$', 'groups_view', name='group'),
    url(r'^manage_group_req$', 'manage_group_req_view', name='manage_group_req'),
    url(r'^manage_group_req/(?P<_type>\w+)/(?P<greq_id>\d+)', 'approve_reject_group_request', name='approve_reject_greq'),

    url(r'^group/create$', 'create_group', name='create_group'),
    url(r'^mygroups$', 'list_my_groups', name='my_groups'),
    url(r'^exit_group/(\d+)$', 'exit_group', name='exit_group'),
    url(r'^exit_group/(\d+)/(\d+)$', 'exit_group', name='exit_group'),
    url(r'^group/setadmin/(\d+)/(\d+)$', 'set_admin', name='set_admin'),
    url(r'^group/unsetadmin/(\d+)/(\d+)$', 'unset_admin', name='unset_admin'),


    url(r'^group/(\d+)$', 'group_detail', name='group_detail'),
    url(r'^group/addmember/(\d+)$', 'add_member', name='add_member'),


)
