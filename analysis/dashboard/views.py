# coding: utf8
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages

from analysis import generic
from analysis.collection.models import Report, ReportType, Collection
from analysis.core.models import Report as View
from analysis.dashboard.factory import build_data_view


def home(request):
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    else:
        return redirect(reverse('account_login'))


@login_required
def dashboard(request):
    context = {
        'collection': Collection.objects.get_or_create(creator=request.user,
                                                       name='Dashboard')[0],
        'ReportType': ReportType,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def view_report(request, view_id):
    report = get_object_or_404(View, id=view_id)

    if not request.user.is_staff:
        if not (set(report.database.groups.values_list('id', flat=True))
                & set(request.user.groups.values_list('id', flat=True))):
            messages.error(request, u'您没有权限，请先申请加入对应组。')
            return redirect(reverse('group'))
    try:
        view = build_data_view(report)
        cache_key = request.build_absolute_uri() + str(request.is_ajax())
        cached = cache.get(cache_key)
        if cached:
            return cached

        resp = generic.report(request, view)
        cache.set(cache_key, resp, 60 * 2)
        return resp

    except Exception, e:
        if e.args and e.args[0] in (1049, 1146):
            messages.error(request, "错误: %s" % e.args[1])
            return redirect(reverse("views"))

        raise


@login_required
def my_reports(request):
    reports = View.objects.all()

    if not request.user.is_staff:
        reports = reports.filter(database__groups__in=request.user.groups.all())

    if request.GET.get('group'):
        reports = reports.filter(database__groups=request.GET.get('group'))

    context = {
        'reports': reports,
    }
    return render(request, 'dashboard/my_reports.html', context)
