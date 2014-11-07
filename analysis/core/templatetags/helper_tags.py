# encoding: utf8
from datetime import date, timedelta
import re
from django import template
from django import forms
from django.contrib.auth.models import Group
from django.db.models import Count
from analysis.collection.models import Link, Collection
from analysis.core.forms import DbGroupForm
from django.db.models.query_utils import Q

register = template.Library()


@register.filter
def is_boolean_field(field):
    return isinstance(field.field, forms.BooleanField)


@register.filter
def bs_control(field):
    klass = field.field.widget.attrs.get('class', '')
    field.field.widget.attrs['class'] = 'form-control ' + klass

    if field.field.required:
        field.field.widget.attrs['required'] = ''

    return field


@register.inclusion_tag('sidebar.html', takes_context=True)
def render_sidebar(context, tab):
    if '.' in tab:
        section, tab = tab.split('.', 1)
    else:
        section, tab = tab, ''

    return {
        'user': context.get('user'),
        'section': section,
        'tab': tab,
    }


@register.filter
def get_item(obj, item):
    return obj[item]


@register.filter(name='getattr')
def _getattr(obj, attr):
    return getattr(obj, attr)


@register.filter
def lookup(d, key):
    key = int(key)
    return d[key]

@register.simple_tag
def get_dbgroup_form(db_instance):
    df = DbGroupForm(instance=db_instance)
    _html = df.as_p()
    print _html
    _html = _html.replace('<p', '<p class="hidden"')
    _html = _html.replace('<ul id="id_groups">', '').replace('</ul>', '')
    _html = _html.replace('<li>', '<div class="checkbox">').replace('</li>', '</div>')
    return _html



@register.inclusion_tag('group_reports_sidebar.html', takes_context=True)
def render_group_reports_menu(context):
    user = context['user']
    return {
        'groups': user.groups.annotate(reports_count=Count('databases__reports'))
    }


@register.simple_tag
def count_collections_in_group(group):
    collection_count = Collection.objects.filter(group=group).count()
    link_count = Link.objects.filter(group=group).count()
    return collection_count+link_count

@register.assignment_tag
def get_none_group_collection_list(user):
    return list(Collection.objects.filter(creator=user, group=None))+list(Link.objects.filter(group=None))


@register.simple_tag
def create_or_edit(instance, create_verb='添加', edit_verb='修改'):
    if instance is None:
        return create_verb
    return edit_verb


@register.simple_tag
def divide(num1, num2):
    return num1 / num2


@register.filter
def is_list(obj):
    return isinstance(obj, (list, tuple))


def last_month(day):
    if day.month > 1:
        return day.replace(month=day.month - 1)

    else:
        return day.replace(year=day.year - 1, month=12)


@register.filter
def parse_relative_date(url):
    today = date.today()
    _range = None

    normalize = lambda dates: '~'.join(map(lambda d: d.strftime('%Y-%m-%d'), dates))

    defined = {
        '$today': [today, today],
        '$yesterday': [today - timedelta(days=1), today - timedelta(days=1)],
        '$thisMonth': [today.replace(day=1), today],
        '$lastMonth': [last_month(today).replace(day=1), today.replace(day=1) - timedelta(days=1)]
    }
    for key in defined.keys():
        if key in url:
            _range = defined[key]
            return url.replace(key, normalize(_range))

    else:
        regex = "$-\d*~$-\d*"
        matches = re.search(regex, url)
        if matches:
            date_string = matches.group()
            start_delta, end_delta = date_string.split('~')
            _range = today + timedelta(days=start_delta[0:]), today + timedelta(days=end_delta[0:])
            return re.sub(regex, normalize(_range), url, 1)

    return url

@register.assignment_tag
def all_groups():
    return Group.objects.all()
