# coding: utf8
from __future__ import unicode_literals
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.utils import timezone


class CollectionManager(models.Manager):
    def for_user(self, user):
        return self.filter(
            Q(creator=user) | Q(group__in=user.groups.all())
        ).order_by('group')


class Collection(models.Model):
    """
    报表集合
    """
    creator = models.ForeignKey(User)
    group = models.ForeignKey(Group, null=True, blank=True)
    name = models.CharField(max_length=100)
    is_featured = models.BooleanField(default=False)
    create_at = models.DateTimeField(default=timezone.now)

    objects = CollectionManager()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return 'collection_detail', [self.id]


class ReportType:
    """
    数据集类型，包括:
    表格
    外链
    图形
    """
    IFRAME = 0
    TABLE = 1
    GRAPHIC = 2


class Report(models.Model):
    """
    数据集
    """
    creator = models.ForeignKey(User, related_name='reports')
    collection = models.ForeignKey(Collection, related_name='reports')

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    type = models.SmallIntegerField()

    order = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=400)
    height = models.PositiveIntegerField(default=300)

    create_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return self.name


class Link(models.Model):
    """
    外部链接
    """
    creator = models.ForeignKey(User, related_name="links")
    group = models.ForeignKey(Group, null=True, blank=True)
    name = models.CharField(max_length=100)
    url = models.URLField()

    created_at = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return self.name
