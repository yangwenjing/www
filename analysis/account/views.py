# coding: utf8
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
# Create your views here.
from analysis.account.models import GroupAddRequest, GroupRequestStatus, GroupAdmin
from django.contrib import messages


context = {}


def logout_view(request):
    logout(request)
    return redirect("/accounts/login")


def login_view(request):
    next = ""
    errors = None
    if request.GET:
        next = request.GET['next']

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        errors = {}
        if user is not None:
            if user.is_active:
                login(request, user)
                print 'login Successfully!'
                if next == '' or next is None:
                    return redirect('/')

                return redirect('/%s' % next)
            else:
                errors['user_active'] = "您的账户未激活,请联系管理员."
        else:
            errors['user_valid'] = "用户名或密码错误"

    return render_to_response(
        'login.html',
        {
            'errors': errors,
            'next': next,
        },
        context_instance=RequestContext(request)
    )


@login_required
def manage_users_view(request):
    context['users'] = User.objects.all()

    return render(request, 'manage_users.html', context)

@require_POST
@staff_member_required
def approve_reject_group_request(request, _type=None, greq_id=None):
    """

    :param request:
    :param _type:
    :param greq_id:
    :return:
    """
    if _type is not None and greq_id is not None:
        group_request = GroupAddRequest.objects.select_related().get(pk=greq_id)
        user = group_request.user
        group = group_request.group
        if _type == 'approve':
            if group_request.status == GroupRequestStatus.APPROVE:
                pass
            else:
                group.user_set.add(user)
                group_request.approve()
                messages.success(request, u"批准用户 %s 加入组 %s 的请求" % (user.username, group.name))
                print "User %s is in Group %s" % (user, group.name)
        elif _type == 'reject':
            if group_request.status == GroupRequestStatus.REJECT:
                pass
            else:
                group.user_set.remove(user)
                group_request.reject()
                messages.success(request, u"拒绝用户 %s 加入组 %s 的请求" % (user.username, group.name))

    return redirect(reverse('manage_group_req'))



@staff_member_required
def manage_group_req_view(request):

    context['group_requests'] = GroupAddRequest.objects.filter(status=GroupRequestStatus.NEW)
    context['group_req_status'] = [u'其他', u'待审核', u'批准', u'拒绝']
    context['dealed_greqs'] = GroupAddRequest.objects.exclude(status=GroupRequestStatus.NEW)

    return render(request, 'group/list_join_group_request.html', context)

@login_required
def create_group(request, group_id=None):
    group = get_object_or_404(Group, id=group_id) if group_id else None
    try:
        if request.method == 'POST':
            name = request.POST.get('name')
            if Group.objects.filter(name=name).exists():
                raise ValidationError("该名称已经被占用！")
            if group is None:
                group = Group.objects.create(name=name)
                GroupAdmin.objects.create(
                    user=request.user,
                    group=group
                )
                group.user_set.add(request.user)
                messages.success(request, "创建成功！")

            else:
                group.name = name
                group.save()
                messages.success(request, "修改成功！")

            return redirect(reverse('my_groups'))

    except ValidationError, e:

        messages.error(request, '\n'.join(e.messages))
        return redirect(reverse('create_group'))

    return render(request, 'group/create_group.html', {'group': group})


@require_POST
@login_required
def exit_group(request, group_id, user_id=None):
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id) if user_id else request.user

    #如果请求人是admin
    if GroupAdmin.objects.is_admin(group, request.user):
        # 如果只有一个管理员
        if GroupAdmin.objects.filter(group=group).count() == 1:
            #被踢的是管理员
            if GroupAdmin.objects.is_admin(group=group,user=user):
                messages.error(request, "仅有一个管理员，不能退组！")
            else:
                #不是管理员
                group.user_set.remove(user)
                messages.success(request, "踢人成功！")
        else:
            #有多个管理员
            GroupAdmin.objects.get(user=user, group=group).delete()
            group.user_set.remove(user)
            messages.success(request, "管理员退组成功！")


    elif request.user == user:
        #如果请求人自己要退组
        group.user_set.remove(user)
        messages.success(request, "成功退组!")
    else:
        #想踢别人出组，又不是管理员
        messages.error(request, "您没有权限踢人！")

    return redirect(request.META.get('HTTP_REFERER'))


@require_POST
@login_required
def set_admin(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id)

    if not GroupAdmin.objects.is_admin(group=group, user=request.user):
        messages.warning(request, "您没有权限设置该组管理员！")
    elif GroupAdmin.objects.is_admin(group=group, user=user):
        messages.warning(request, "该用户已经是管理员！")
    else:

        GroupAdmin.objects.create(
            group=group,
            user=user
        )
        messages.success(request, "管理员设置成功！")
    return redirect(request.META.get('HTTP_REFERER'))


@require_POST
@login_required
def unset_admin(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id)
    if not GroupAdmin.objects.is_admin(group=group, user=request.user):
        messages.warning(request, "您没有权限设置该组管理员！")
    elif not GroupAdmin.objects.is_admin(group=group, user=user):
        messages.warning(request, "该用户不是管理员！")
    elif GroupAdmin.objects.filter(group=group).count() <= 1:
        messages.warning(request, "该用户为唯一的管理员，不能取消！")
    else:
        GroupAdmin.objects.get(
            group=group,
            user=user
        ).delete()
        messages.success(request, "取消管理员成功！")
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def groups_view(request):
    if request.POST:
        group = Group.objects.get(name=request.POST['group'])
        add_group_req(request.user, group)
        messages.success(request, u'已经申请加入组%s' % group.name)

    context['groups'] = Group.objects.all()
    greq_list = GroupAddRequest.objects.filter(
        user=request.user,
        status=GroupRequestStatus.NEW
    ).select_related('group')

    req_groups = []
    for greq in greq_list:
        req_groups.append(greq.group)
    context['req_groups'] = req_groups

    rej_greq_list = GroupAddRequest.objects.filter(
        user=request.user,
        status=GroupRequestStatus.REJECT
    ).select_related('group')

    rej_groups = []
    for greq in rej_greq_list:
        rej_groups.append(greq.group)

    context['rej_groups'] = rej_groups

    return render(request, 'group/list_groups.html', context)


def add_group_req(user, group):
    try:
        greq = GroupAddRequest.objects.get(user=user, group=group)
        greq.audit()

    except ObjectDoesNotExist, e:
        greq = GroupAddRequest(user=user, group=group)
        greq.audit()
        print e


def approve_group_req(user, group):
    try:
        greq = GroupAddRequest.objects.get(user=user, group=group)
        greq.approve()

    except ObjectDoesNotExist, e:
        print e


def reject_group_req(user, group):
    try:
        greq = GroupAddRequest.objects.get(user=user, group=group)
        greq.reject()

    except ObjectDoesNotExist, e:
        print e


@login_required
def list_my_groups(request):
    context = {
        'my_groups': request.user.groups.all()
    }
    return render(request, 'list_my_groups.html', context)


@login_required
def group_detail(request, group_id):

    group = get_object_or_404(Group, id=group_id)
    if not request.user in group.user_set.all():
        messages.warning(request, u'您不是组【%s】成员，不能查看组详情!' % group.name)
        return redirect(reverse('group'))

    all_user = User.objects.all()
    group_member = group.user_set.all()
    context = {
        'group': group,
        'other_users': list(set(all_user).difference(set(group_member)))
    }
    return render(request, 'group_detail.html', context)

@login_required
@require_POST
def add_member(request, group_id):
    group = get_object_or_404(Group, id = group_id)

    if not GroupAdmin.objects.is_admin(group=group, user=request.user):
        messages.error(request, "您没有权限添加用户！")
        return redirect(request.META.get('HTTP_REFERER'))

    member_id = request.POST.get('member')
    if member_id is None or member_id == '':
        return redirect(request.META.get('HTTP_REFERER'))
    member = get_object_or_404(User, id=member_id)
    group.user_set.add(member)
    messages.success(request, "用户添加成功！")
    is_admin = request.POST.get('admin')
    if is_admin:
        GroupAdmin.objects.create(
            group=group,
            user=member
        )
    return redirect(request.META.get('HTTP_REFERER'))