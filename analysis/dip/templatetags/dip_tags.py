from django import template
from django.utils import simplejson

from analysis.dip.models import ImportHistory, ImportStatus


register = template.Library()


@register.assignment_tag
def get_import_status_hourly(job, date):
    f_date = date.strftime('%Y%m%d')
    records = ImportHistory.objects.filter(job=job.id, timestamp__contains=f_date)
    result = 0
    records_dict = {}
    context = {}
    if records.count() == 0:
        status = 'no_record'

    else:
        success_count = ImportHistory.objects.filter(job=job, timestamp__contains=f_date,
                                                     status=ImportStatus.SUCCESS).count()
        if success_count == 24:
            status = 'success'
        else:
            status = 'fail'
            result = float(success_count)

        for i in xrange(records.count()):
            record = {
                'timestamp': records[i].timestamp,
                'status': records[i].status,
                'import_rows': records[i].import_rows,
                'ignore_rows': records[i].ignore_rows,
            }
            records_dict[int(records[i].timestamp[8:10])] = record
    for i in xrange(24):
        if i not in records_dict:
            if i >= 10:
                postfix = '%d' % i
            else:
                postfix = '0%d' % i

            timestamp = f_date + postfix
            record = {
                'status': 0,
                'timestamp': timestamp,
                'import_rows': 0,
                'ignore_rows': 0
            }
            records_dict[i] = record

    context['status'] = status
    context['result'] = result
    context['records'] = records_dict.values()
    return context


@register.assignment_tag
def get_import_status_daily(job, datelist):
    context = []
    for f_date in datelist:
        record = {}
        f_date = f_date.strftime('%Y%m%d')
        records = ImportHistory.objects.filter(job=job.id, timestamp__contains=f_date)

        import_rows = 0
        ignore_rows = 0
        if records is None or records.count() == 0:
            status = 0
        else:
            status = records[0].status
            import_rows = records[0].import_rows
            ignore_rows = records[0].ignore_rows

        record['status'] = status
        record['timestamp'] = f_date
        record['import_rows'] = import_rows
        record['ignore_rows'] = ignore_rows
        context.append(record)
    return context




