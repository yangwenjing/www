#coding: utf-8
from datetime import timedelta, date

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.views.decorators.http import require_POST
from analysis.aggregate.forms import AggregateJobForm
from analysis.aggregate.models import AggregateJob, AggregateHistory

@staff_member_required
def create_aggregation(request, aggregate_id=None):
    aggregate_job = get_object_or_404(AggregateJob, id=aggregate_id) if aggregate_id else None

    if request.method == 'POST':
        form = AggregateJobForm(request.POST, instance=aggregate_job)

        if form.is_valid():
            aggregate_job = form.save(commit=False)

            if not aggregate_job.id:
                aggregate_job.creator = request.user

            aggregate_job.fields = ','.join(request.POST.getlist('field'))
            aggregate_job.save()

            messages.success(request, "任务已保存")

            return redirect(reverse('aggregate_list'))

    else:
        initial = {}
        if not aggregate_job:
            initial = {
                'database': request.GET.get('db')
            }

        form = AggregateJobForm(instance=aggregate_job, initial=initial)

    context = {
        'job': aggregate_job,
        'form': form,
    }
    return render(request, 'create_aggregation.html', context)


@staff_member_required
def aggregate_history(request):
    #aggregate job ---> many aggregate_history
    datelist = [date.today() - timedelta(i) for i in range(7)]
    return render(request,
                  'aggregate_history.html',
                  {'aggregate_jobs': AggregateJob.objects.all(),
                   'datelist': datelist})


@staff_member_required
def list_aggregate_job(request):
    aggregate_jobs = AggregateJob.objects.all()
    return render(request,
                  'list_aggregatejobs.html',
                  {'aggregate_jobs': aggregate_jobs})

@require_POST
@staff_member_required
def delete_aggregation(request, jobid):
    job = get_object_or_404(AggregateJob, id=jobid)
    job.delete()
    messages.success(request, "删除成功！")
    return redirect(reverse('aggregate_list'))