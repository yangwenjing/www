# coding: utf8
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from analysis.core.forms import DatabaseForm, ReportForm, DbGroupForm

from analysis.core.models import Database, Report, Field
from analysis.core.utils import render_json


@login_required
def manage_databases(request):
    context = {
        'databases': Database.objects.all().select_related('group'),
        'groups': Group.objects.all()
    }
    return render(request, 'core/manage_databases.html', context)


@login_required
def create_database(request, db_id=None):
    origin_instance = get_object_or_404(Database, id=db_id) if db_id else None

    if request.method == 'POST':
        form = DatabaseForm(request.POST, instance=origin_instance)
        group_ids = request.POST.getlist('groups')

        if form.is_valid():

            db = form.save(commit=False)
            if not db.pk:
                db.engine = 'mysql'
                db.creator = request.user

            db.save()
            db.groups = Group.objects.filter(id__in=group_ids)
            db.save()

            return redirect(reverse('databases'))

    else:
        form = DatabaseForm(instance=origin_instance)

    return render(request, "core/create_database.html", {'form': form, 'all_groups': Group.objects.all()})



@staff_member_required
def list_tables(request):
    db_id = request.GET.get('database')
    db = get_object_or_404(Database, id=db_id)

    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute('show tables;')

    result = []

    for table in cursor.fetchall():
        table = table[0]
        cursor.execute('show columns from `%s`' % table)

        result.append({
            'name': table,
            'fields': [{'name': row[0].strip(), 'type': row[1]} for row in cursor]
        })

    return render_json(result)


@staff_member_required
def list_database_groups(request):
    db_id = request.GET.get('db')
    db = get_object_or_404(Database, id=db_id)
    result = []

    result.append({
        'db_id':db_id,
        'all_groups':db.groups.all(),
        'added_groups_list':list(db.groups.all())
    })
    return render_json(result)


@staff_member_required
def create_report(request, report_id=None):
    """
    创建报表
    :param report_id: 如果不为 None 则是编辑报表
    """
    if not Database.objects.count():
        messages.error(request, "还没有创建数据库哦，无法创建报表")
        return redirect(reverse('databases'))

    instance = get_object_or_404(Report, id=report_id) if report_id else None

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=instance)

        if form.is_valid():
            with transaction.atomic():
                report = form.save(commit=False)
                if not report.pk:
                    report.creator = request.user

                report.save()

                # delete old dimensions
                report.fields.all().delete()

                field_count = request.POST.get('field_count', '0')
                types = ['dimension', 'property']

                for x in xrange(int(field_count)):
                    fields = ['display', 'source', 'type', 'data_type', 'expression']
                    display, source, type, data_type, express = [
                        request.POST.get("field_%d_%s" % (x, f)) or '' for f in fields]

                    if not type in types:
                        continue

                    Field.objects.create(
                        report=report,
                        order=x,
                        type=types.index(type) + 1,
                        source=source.strip(),
                        display=display,
                        data_type=data_type,
                        expression=express.strip(),
                    )

            messages.success(request, "数据报表创建成功")
            return redirect(reverse('views'))

    else:
        form = ReportForm(instance=instance, initial={
            # 'database': Database.objects.get(id=request.GET.get('db'))
            'database': request.GET.get('db')
        })

    context = {
        'report': instance,
        'form': form
    }
    return render(request, "core/create_view.html", context)


@staff_member_required
def manage_views(request):
    context = {
        'reports': Report.objects.all(),
    }
    return render(request, "core/manage_views.html", context)

@require_POST
@staff_member_required
def delete_view(request, view_id=None):
    report = get_object_or_404(Report, id=view_id)

    report.delete()

    messages.success(request, "报表已删除")
    return redirect(reverse('views'))

@require_POST
@staff_member_required
def delete_database(request, database_id=None):
    database = get_object_or_404(Database, id=database_id)

    if database.reports.count()>0:
        messages.error(request, "请先删除数据库中的表，再删除数据库。")
    else:
        database.delete()
        messages.success(request, "数据库已删除")
    return redirect(reverse('databases'))


@staff_member_required
def manage_database_group(request, database_id=None):
    database_instance = get_object_or_404(Database, id=database_id)

    if request.method == 'POST':
        form = DbGroupForm(request.POST, instance=database_instance)
        if form.is_valid():
            db = form.save()
            db.save()
            messages.success(request, "数据库的用户组改变成功")

        else:
            for (k, v) in form.errors.items():
                messages.error(request, "存在错误%s : %s" % (k, v))
    else:
        form = DbGroupForm(instance=database_instance)

    return redirect(reverse('databases'))


@login_required
def show_sample_data(request):
    database = request.GET.get('database')
    table = request.GET.get('table')

    db = get_object_or_404(Database, id=database)
    conn = db.connect()
    cursor = conn.cursor()

    cursor.execute('select * from `%s` limit 20' % table)
    rows = cursor.fetchall()
    context = {
        'cursor': cursor
    }
    return render(request, 'dashboard/sample_data.html', context)
    # return HttpResponse(cursor.fetchall(), mimetype='text/plain')
