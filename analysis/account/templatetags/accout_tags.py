from django import template

from analysis.account.models import GroupAddRequest, GroupRequestStatus, GroupAdmin


register = template.Library()


@register.simple_tag
def new_group_requests_count():
    counter = GroupAddRequest.objects.filter(status=GroupRequestStatus.NEW).count()
    if counter==0:
        return ""
    else:
        return "<span class='badge bg-yellow pull-right'>%d</span>" % counter

@register.assignment_tag
def is_admin(group, user):
    return GroupAdmin.objects.is_admin(group, user)
