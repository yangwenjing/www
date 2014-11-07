# coding: utf8
from __future__ import unicode_literals

import json
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models.query_utils import Q
from django.shortcuts import render, get_object_or_404, redirect
from analysis.account.utils import in_group
from analysis.collection.models import Report, Collection, ReportType, Link
from analysis.core.utils import render_json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404

from django.views.decorators.http import require_POST
from analysis.collection.forms import CollectionForm, ReportForm, LinkForm


@login_required
def show_collection_detail(request, collection_id):
    '''
    :param request:
    :param collection_id:
    :return:detail of a collection
    '''
    collection = get_object_or_404(Collection, id=collection_id)
    reports = Report.objects.filter(collection=collection).select_related('creator')
    context = {
        'collection': collection,
        'reports': reports
    }
    return render(request, 'collection/collection_detail.html', context)


@login_required
def list_collection(request):
    """
    列出所有用户和用户所在组的收藏夹
    """

    collections = Collection.objects.for_user(request.user)
    user_groups = request.user.groups.all()

    context = {
        'collections': collections,
        'user': request.user,
        'user_groups': user_groups
    }

    return render(request, 'collection/list_collections.html', context)

@login_required
def list_collection_link_for_group(request, group_id):
    """
    列出所有用户和用户所在组的收藏夹
    """
    group = get_object_or_404(Group, id=group_id)
    collections = Collection.objects.filter(group=group)
    links = Link.objects.filter(group=group)

    context = {
        'group': group,
        'collections': collections,
        'links': links
    }

    return render(request, 'list_group_collections.html', context)


def create_collection(request, collection_id=None):
    instance = get_object_or_404(Collection, id=collection_id) if collection_id else None

    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=instance)
        try:
            if form.is_valid():
                # 判断自己是否已经创建该收藏夹
                collection = form.save(commit=False)
                if collection.creator != request.user:
                    raise ValidationError(u'用户无权创建此收藏夹!')
                if instance and instance.creator != request.user:
                    raise ValidationError("您没有权限修改或创建该收藏夹!")
                messages.success(request, "收藏夹创建成功！")
                collection.save()
            else:
                error_message = []
                for (k,v) in form.errors.items():
                    error_message += v
                messages.error(request, '\n'.join(error_message))
        except ValidationError, e:
            messages.error(request, '\n'.join(e.messages))
        finally:
            return redirect(reverse("list_collection"))
    else:
        form = CollectionForm(instance=instance)
        return render(request, '', {'form': form})


@require_POST
@login_required
def feature_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if collection.is_featured:
        collection.is_featured = False
    else:
        collection.is_featured = True
    collection.save()
    return redirect(reverse('list_collection'))

@require_POST
@login_required
def delete_collection(request,collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if request.user.id != collection.creator.id:
        messages.error(request, "您没有权限删除此收藏夹！")
    else:
        collection.delete()
        messages.success(request, "收藏夹删除成功！")
    return redirect(reverse('list_collection'))


def create_report(request, report_id=None):
    instance = get_object_or_404(Report, id=report_id) if report_id else None

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=instance)
        collection_id = request.POST.get('collection')
        try:
            if form.is_valid():
                report = form.save(commit=False)

                creator = form.cleaned_data.get('creator')
                if creator != request.user:
                    raise ValidationError("您没有权限修改或创建该收藏夹!")
                if instance and instance.creator != request.user:
                    raise ValidationError("您没有权限修改或创建该收藏夹!")
                report.type = ReportType.IFRAME
                report.save()
                if report_id:
                    messages.success(request, "编辑外部报表成功！")
                else:
                    messages.success(request, "新建外部报表成功！")
            else:
                error_message = []
                for (k,v) in form.errors.items():
                    error_message += v
                messages.error(request, '\n'.join(error_message))

        except ValidationError, e:
            messages.error(request, '\n'.join(e.messages))
        finally:
            return redirect(reverse('collection_detail', args=(collection_id,)))
    else:
        form = ReportForm(instance=instance)
        return render(request, '', {'form': form})


@login_required
def star_report(request):
    url = request.POST.get('url')
    cid = request.POST.get('collection')
    name = request.POST.get('name')
    type = request.POST.get('type')

    if not cid:
        collection, created = Collection.objects.get_or_create(
            creator=request.user, name='Dashboard',
        )

    else:
        #TODO: 检查用户是否有这个 Collection 的权限
        collection = get_object_or_404(Collection, id=cid)

    Report.objects.create(
        creator=request.user,
        collection=collection,
        name=name, url=url,
        type=ReportType.TABLE if type == 'table' else ReportType.GRAPHIC,
    )

    return redirect(request.META.get('HTTP_REFERER'))
    # return render_json({'success': True})


@login_required
def collection_report(request, cid):
    collection = get_object_or_404(Collection, id=cid)

    if not Collection.objects.for_user(request.user).filter(id=cid).exists():
        messages.error(request, "您无权查看此收藏夹")

    context = {
        'collection': collection,
        'ReportType': ReportType
    }
    return render(request, "collection/collection_report.html", context)


@require_POST
@login_required
def change_report_size(request):
    report_id = request.POST.get('report', '')
    width = request.POST.get('width', '')
    height = request.POST.get('height', '')

    if not report_id.isdigit() or not width.isdigit() or not height.isdigit():
        return HttpResponse(status=400)

    report = get_object_or_404(Report, id=report_id)
    if report.creator_id == request.user.id or in_group(request.user, report.collection.group):
        report.width = abs(int(width))
        report.height = abs(int(height))
        report.save()

        return render_json({'success': True})

    return render_json({'success': False, 'error': '没有权限'})


@require_POST
@login_required
def sort_widgets(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    sorted_ids = request.POST.get('sorted', '').split(',')
    reports = dict((report.id, report) for report in collection.reports.all())

    for idx, report_id in enumerate(sorted_ids):
        report = reports[int(report_id)]
        report.order = idx
        report.save()

    return render_json({'success': True})


@require_POST
@login_required
def remove_widget(request, wid):
    widget = get_object_or_404(Report, id=wid)

    if widget.creator_id == request.user.id or in_group(request.user, widget.collection.group):
        widget.delete()

        return render_json({'success': True})

    return render_json({'success': False, 'error': '您没有权限删除此挂件'})


@login_required
def list_external_links(request):
    user_links = Link.objects.filter(
        Q(creator=request.user) | Q(group__in=request.user.groups.all())
    ).order_by('group')

    return render(request,
                  'external/list_external_links.html',
                  {'external_links': user_links})

@login_required
def create_link(request, link_id=None):
    instance = get_object_or_404(Link, id=link_id) if link_id else None
    if request.method == 'POST':
        form = LinkForm(request.POST, instance=instance)

        if form.is_valid():
            # 判断自己是否已经创建该收藏夹
            link = form.save(commit=False)
            if instance:
                if instance.creator != request.user:
                    raise ValidationError("您没有权限修改或创建该外部链接!")
            else:
                link.creator = request.user

            link.save()
            messages.success(request, "外部链接创建成功！")
            return redirect(reverse("list_external_links"))
        else:
            messages.error(request, form.errors)
    else:
        form = LinkForm(request.POST, instance=instance)
        return render(request, 'external/create_link.html', {'form': form})

@login_required
def show_link(request, id):
    link = get_object_or_404(Link, id=id)
    return render(request, 'external/link_detail.html', {'link': link})


@require_POST
@login_required
def delete_link(request, id):
    link = get_object_or_404(Link, id=id)

    if link.creator == request.user:
        link.delete()
        messages.success(request,"%s删除成功！" % link.name)

    else:
        messages.error(request,"没有权限删除链接-%s" % link.name)
    return redirect(request.META.get('HTTP_REFERER'))
