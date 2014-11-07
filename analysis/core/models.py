# coding: utf8
from __future__ import unicode_literals
import MySQLdb

from django.contrib.auth.models import User, Group
from django.db import models
from django.utils import timezone


ENGINE_CHOICES = (
    ('MySQL', 'mysql'),
)


class DatabaseManager(models.Manager):
    pass


class Database(models.Model):
    creator = models.ForeignKey(User, related_name='dbs')

    engine = models.CharField('类型', max_length=100, choices=ENGINE_CHOICES)
    host = models.CharField('主机', max_length=100,
                            help_text="尽量填可以通过外部访问的IP/域名，不要填 localhost")
    port = models.PositiveIntegerField('端口', default=3306)
    name = models.CharField('数据库', max_length=100)
    user = models.CharField('用户名', max_length=100)
    password = models.CharField('密码', max_length=100, blank=True)

    groups = models.ManyToManyField(Group, db_constraint=False, related_name='databases')

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        pass

    def stringify(self):
        return '%s://%s:%s@%s:%s/%s' % (
            self.engine, self.user, self.password, self.host, self.port, self.name
        )

    def __unicode__(self):
        return "%s://%s@%s:%s/%s" % (
            self.engine,
            self.user,
            self.host,
            self.port,
            self.name
        )

    def connect(self):
        return MySQLdb.connect(
            host=self.host, port=self.port, db=self.name,
            user=self.user, passwd=self.password,
            charset='utf8')


class Report(models.Model):
    creator = models.ForeignKey(User, verbose_name='创建人')
    name = models.CharField('报告名字', max_length=100)

    database = models.ForeignKey(Database, verbose_name='数据库',
                                 related_name='reports')
    table = models.CharField('表', max_length=100)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "数据报表"

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return 'dashboard_report', [self.id]


class FieldType:
    DIMENSION = 1
    PROPERTY = 2


class Field(models.Model):
    """
    数据报表的字段

    source
        表中的字段，如果是指标则可以包括多个字段，
        包括多个字段时使用 expression 计算最终值

    type 指定是维度还是指标
    data_type 是指标的类型 (size, time, number, percent)
    expression 指标的计算规则
    """
    report = models.ForeignKey(Report, verbose_name='报告',
                               related_name="fields")
    order = models.SmallIntegerField('字段顺序')

    type = models.SmallIntegerField('字段类型', choices=(
        (FieldType.DIMENSION, '维度'),
        (FieldType.PROPERTY, '指标'),
    ))

    source = models.CharField('表字段', max_length=100)
    display = models.CharField('显示名称', max_length=100)

    data_type = models.CharField('数据类型', max_length=20, null=True, blank=True)
    expression = models.CharField('表达式', null=True, blank=True, max_length=200)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return self.display

    def type_string(self):
        if self.type == FieldType.DIMENSION:
            return 'dimension'
        elif self.type == FieldType.PROPERTY:
            return 'property'
        return 'ignore'
