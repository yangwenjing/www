# coding: utf8
from __future__ import unicode_literals
from django.contrib.auth.models import User

from django.db import models
from django.utils import timezone
from analysis.core.models import Database


class JobStatus:
    WAITING = 1
    RUNNING = 2


JOB_STATUS_CHOICES = (
    (JobStatus.WAITING, '等待下次导入'),
    (JobStatus.RUNNING, '导入中')
)


class Job(models.Model):
    """
    DIP 任务导入程序

    fields: 逗号分隔的表的字段列表,一一对应 DIP 分析任务的输出字段
    """
    creator = models.ForeignKey(User, related_name="import_jobs")

    database = models.ForeignKey(Database, verbose_name="数据库")
    table = models.CharField('表', max_length=100)

    dip_id = models.CharField("DIP 任务 ID", max_length=32)
    dip_alias = models.CharField("DIP 任务名字", max_length=100)
    interval = models.PositiveIntegerField("任务频率", choices=(
        (3600, "每小时"),
        (3600 * 24, '每天')
    ))
    fields = models.TextField('字段')

    status = models.SmallIntegerField(default=JobStatus.WAITING,
                                      choices=JOB_STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        pass

    def __unicode__(self):
        return "#%d %s" % (self.id, self.table)

    @property
    def fields_list(self):
        return self.fields.split(',')


class ImportStatus:
    RUNNING = 1
    SUCCESS = 2
    FAILED = 3


class ImportHistory(models.Model):
    job = models.ForeignKey(Job, verbose_name="任务")

    timestamp = models.CharField('任务时间', max_length=20)

    import_rows = models.PositiveIntegerField()
    ignore_rows = models.PositiveIntegerField()

    status = models.SmallIntegerField('状态', choices=(
        (ImportStatus.RUNNING, '运行中'),
        (ImportStatus.SUCCESS, '成功'),
        (ImportStatus.FAILED, '失败')
    ))

    import_at = models.DateTimeField(default=timezone.now)

    class Meta:
        pass

