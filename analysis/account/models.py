# coding: utf8
from django.contrib.auth.models import User, Group
from django.db import models


class GroupAdminManager(models.Manager):
    def is_admin(self, group, user):
        return self.filter(group=group, user=user).exists()


class GroupAdmin(models.Model):
    user = models.ForeignKey(User, related_name="admin_groups")
    group = models.ForeignKey(Group, related_name="admins")

    objects = GroupAdminManager()


class GroupRequestStatus:
    NEW = 1
    APPROVE = 2
    REJECT = 3


class GroupAddRequest(models.Model):
    user = models.ForeignKey(User, verbose_name="申请人")
    group = models.ForeignKey(Group)
    status = models.SmallIntegerField(default=GroupRequestStatus.NEW)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s :%s :%s" % (
            self.user,
            self.group,
            self.status,
        )

    def audit(self):
        self.status = GroupRequestStatus.NEW
        self.save()

    def approve(self):
        self.status = GroupRequestStatus.APPROVE
        self.save()

    def reject(self):
        self.status = GroupRequestStatus.REJECT
        self.save()




