# coding: utf8
from __future__ import unicode_literals, print_function
from django.contrib.auth.models import User

from django.db import models
from django.utils import timezone
from analysis.core.models import Database


class AggregateJob(models.Model):
    """
    数据聚合的设置
    设置需要聚合哪个数据库的哪个表格，按什么字段聚合
    """
    creator = models.ForeignKey(User)

    database = models.ForeignKey(Database)
    table = models.CharField(max_length=100)

    datetime_fields = models.CharField(
        "时间字段", max_length=100,
        help_text="多个字段使用','分隔")

    aggregate_fields = models.TextField(
        "聚合维度",
        null=True, blank=True, default='',
        help_text="(可选)要聚合的维度，多个字段使用','分隔")

    sum_fields = models.TextField(
        "聚合字段",
        help_text="要聚合的字段，将使用SUM进行聚合，多个字段使用','分隔")

    remain_days = models.PositiveIntegerField(
        "保留日期",
        help_text="(数字)将保留日期前的数据进行压缩")
    interval = models.PositiveIntegerField("运行频率", default=3600 * 24)

    def __unicode__(self):
        return self.table


class AggregateHistory(models.Model):
    """
    聚合的历史记录，记录着删掉多少行数据，插入多少行数据
    """
    job = models.ForeignKey(AggregateJob, related_name='history')
    aggregate_date = models.DateField("聚合时间")
    delete_rows = models.PositiveIntegerField("删除行数")
    insert_rows = models.PositiveIntegerField("添加行数")
    created_at = models.DateTimeField("运行时间", default=timezone.now)
