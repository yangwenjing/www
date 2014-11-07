from django import template
from analysis.aggregate.models import AggregateHistory

register = template.Library()


@register.assignment_tag
def get_aggregate_history(aggregate_job, date):
    if not AggregateHistory.objects.filter(job=aggregate_job,aggregate_date=date):
        return None

    return AggregateHistory.objects.filter(job=aggregate_job,aggregate_date=date).latest('created_at')