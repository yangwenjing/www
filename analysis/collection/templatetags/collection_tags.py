from django import template
from django.contrib.auth.models import Group
from django.db.models.query_utils import Q
from analysis.collection.models import Collection, Link

register = template.Library()


@register.assignment_tag
def get_collections_for(user):
    return Collection.objects.for_user(user)


@register.assignment_tag
def get_featured_collections():
    return Collection.objects.filter(is_featured=True)

@register.assignment_tag
def get_sidebar_collections(user):
    return Collection.objects.for_user(user)

@register.assignment_tag
def get_user_groups(user):
    return user.groups.all()

@register.assignment_tag
def list_external_links(user):
    return Link.objects.filter(
        Q(creator=user) | Q(group__in=user.groups.all())
    ).order_by('group')

