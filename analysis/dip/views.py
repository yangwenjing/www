# coding: utf8
from __future__ import unicode_literals
from datetime import timedelta, datetime, date
from StringIO import StringIO
from django.core.management import BaseCommand, CommandError
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
import sys
from analysis.dip.forms import JobForm
from analysis.dip.models import Job, ImportHistory, ImportStatus
from django.utils import simplejson

@staff_member_required
def manage_jobs(request):
    jobs = Job.objects.all()

    context = {
        'jobs': jobs,
    }
    return render(request, "dip/jobs.html", context)


@staff_member_required
def create_job(request, job_id=None):
    job = get_object_or_404(Job, id=job_id) if job_id else None

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)

        if form.is_valid():
            job = form.save(commit=False)

            if not job.id:
                job.creator = request.user

            job.fields = ','.join(request.POST.getlist('field'))
            job.save()

            messages.success(request, "任务已保存")

            return redirect(reverse('manage_jobs'))

    else:
        initial = {}
        if not job:
            initial = {
                'database': request.GET.get('db')
            }

        form = JobForm(instance=job, initial=initial)

    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'dip/create_job.html', context)


@require_POST
@staff_member_required
def reimport_job(request):
    job_id = request.GET.get('job_id')
    timestamp = request.GET.get('timestamp')
    if ImportHistory.objects.filter(job=job_id,timestamp=timestamp).exists():
        ImportHistory.objects.filter(job=job_id,timestamp=timestamp).delete()

    return import_job(request)


@require_POST
@staff_member_required
def import_job(request):
    job_id = request.GET.get('job_id')
    timestamp = request.GET.get('timestamp')
    out = StringIO()
    _out = sys.stdout
    _error = sys.stderr
    is_success = False
    message = ''
    output = ''
    try:

        sys.stdout = out
        sys.stderr = out

        call_command('sync_dip', timestamp, job=job_id)

    except CommandError, e:
        message = e.message

    finally:
        sys.stdout = _out
        sys.stderr = _error
        output = out.getvalue()

    import_rows = 0
    ignore_rows = 0
    if ImportHistory.objects.filter(job=job_id, timestamp=timestamp, status=ImportStatus.SUCCESS).exists():
        is_success = True
        message = "#" + job_id + " " + timestamp + "导入成功!"
    elif ImportHistory.objects.filter(job=job_id, timestamp=timestamp).exists():
        import_history = ImportHistory.objects.filter(job=job_id, timestamp=timestamp).latest("import_at")
        ignore_rows = import_history.ignore_rows
        import_rows = import_history.import_rows

    context = {
        'is_success': is_success,
        'message': message,
        'output': output,
        'import_rows': import_rows,
        'ignore_rows': ignore_rows
    }
    return HttpResponse(simplejson.dumps(context))


@require_POST
@staff_member_required
def delete_job(request, job_id=None):
    job = get_object_or_404(Job, id=job_id)

    job.delete()

    messages.success(request, "任务已删除")
    return redirect(reverse('manage_jobs'))


@staff_member_required
def import_history(request):
    if request.GET.get('from_date') and request.GET.get('to_date'):
        f_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        if f_date > to_date:
            messages.error(request, "时间区间选择不合法")
            return get_daylist(7)

        daylist = get_daylist_during(f_date, to_date)

    else:
        days = 8
        daylist = get_daylist(days)
    hour_jobs = Job.objects.filter(interval=3600).distinct()
    daily_jobs = Job.objects.filter(interval=3600 * 24).distinct()

    context = {
        'daylist': daylist,
        'hour_jobs': hour_jobs,
        'daily_jobs': daily_jobs,
        'hours': [i for i in xrange(24)],

    }
    return render(request, 'dip/import_history.html', context)


def get_daylist_during(f_date_str, to_date_str):
    f_date = datetime.strptime(f_date_str, "%Y-%m-%d").date()
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    daylist = []
    index_date = f_date
    while index_date <= to_date:
        daylist.append(index_date)
        index_date = index_date + timedelta(1)
    return daylist


def get_daylist(days):
    i = 0
    daylist = []
    for i in xrange(days):
        _date = date.today() - timedelta(i)
        daylist.append(_date)
    daylist.sort()
    return daylist


