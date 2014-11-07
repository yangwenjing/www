# coding: utf8
from __future__ import unicode_literals, print_function
import os
from optparse import make_option
from warnings import filterwarnings
from datetime import datetime, timedelta

from django.core.management import BaseCommand, CommandError
from django.utils.log import getLogger
from MySQLdb import Warning
from analysis.aggregate.models import AggregateJob, AggregateHistory
from analysis.core.models import Database
from analysis.dip.management.commands.sync_dip import bulk_execute

filterwarnings('ignore', category=Warning)
help = u"""对某个数据库中的某个表进行压缩
USAGE: manage.py compress_table --db id --table table_name --compress=field --date "YYYY-MM-DD" [--dt]
                [--remain [fields]] [--sum [fields]]

压缩数据库，只能压缩Date或者Datatime字段

参数
====

--db: 选择数据库id
--table: 选择数据库名字
--compress: 压缩的字段
--date: 选择压缩的时间
--remain: 保留的字段
--sum：选择加和的字段


[field]: 字段名字
[fields]: 一个或多个字段名字，用','隔开

例如
====
python manage.py compress_table --db 1 --table test_httpcode --compress cdate --date "2014-08-26"  --sum "num" --dt



压缩方法
========

如果表存在，按天压缩。
Group by remain的字段，对sum的字段取和。
"""
logger = getLogger('console')


def log(*args):
    print("Process %d -" % os.getpid(), *args)


def process_aggregatejob(jobid):
        aggregate_job = AggregateJob.objects.get(id=jobid)
        db = aggregate_job.database
        table = aggregate_job.table
        day = datetime.now()
        target_day = day + timedelta(days=-aggregate_job.remain_days)
        _date = target_day.strftime("%Y-%m-%d")
        compress = aggregate_job.datetime_fields.replace(" ", "").split(',')
        remains_fields = aggregate_job.aggregate_fields.replace(" ", "")

        remains_field_list = remains_fields.split(',') if remains_fields != "" else []
        sum_field_list = aggregate_job.sum_fields.replace(" ", "").split(',')
        if len(compress) == 2:
            is_dt = False # date字段仅仅表示date
        else:
            is_dt = True
        delete_rows, insert_rows = compress_table(db, table, compress, _date, remains_field_list, sum_field_list, is_dt)
        AggregateHistory.objects.create(
            job=aggregate_job,
            aggregate_date=_date,
            delete_rows=delete_rows,
            insert_rows=insert_rows
        )

def get_where_clause(compress_field, date, is_dt):
    if is_dt:
        day = datetime.strptime(date, "%Y-%m-%d")
        a_day_later = day + timedelta(days=1)

        return "%s >= '%s' and %s < '%s'" % (compress_field, date, compress_field, a_day_later.strftime("%Y-%m-%d"))
    else:

        return "%s = '%s'" % (compress_field, date)


def insert_sql(table, fields_list):
    sql = "INSERT INTO `{table}` ({fields}) VALUES ({values})"
    fields = ['`%s`' % f for f in fields_list]
    values = ['%s'] * len(fields_list)

    return sql.format(table=table, fields=', '.join(fields), values=', '.join(values))


def delete_sql(table, compress_field, date, is_dt):
    sql = "DELETE FROM `{table}` WHERE {where_clause} "

    return sql.format(table=table,
                      where_clause=get_where_clause(compress_field, date, is_dt))


def select_sql(table, compress, date, remains_field_list, sum_field_list, is_dt):
    fields = ['`' + compress[0] + '`']
    if len(compress) == 2:

        fields += ['"00:00:00"']

    fields += ['`%s`' % f for f in remains_field_list] + \
              ['SUM(`' + f + '`)' for f in sum_field_list]
    where_clause = get_where_clause(compress[0], date, is_dt)
    if remains_field_list:
        sql = "SELECT {fields} FROM `{table}` WHERE {where_clause} GROUP BY {remains_fields}"
        return sql.format(table=table, fields=','.join(fields),
                          where_clause=where_clause,
                          remains_fields=','.join(remains_field_list))
    else:
        sql = "SELECT {fields} FROM `{table}` WHERE {where_clause}"

        return sql.format(table=table, fields=','.join(fields),
                          where_clause=where_clause)


def compress_table(db, table, compress, _date, remains_field_list, sum_field_list, is_dt):
    sel_sql = select_sql(table, compress, _date, remains_field_list, sum_field_list, is_dt)
    del_sql = delete_sql(table, compress[0], _date, is_dt)
    inst_sql = insert_sql(table, compress + remains_field_list + sum_field_list)

    conn = db.connect()
    try:
        cursor = conn.cursor()
        cursor.execute('SET NAMES UTF8')
        buffer = []
        print('EXECUTE:', sel_sql, '...')

        rows_count = cursor.execute(sel_sql)
        print("Result: %d rows" % rows_count)

        conn.autocommit(False)
        for row in cursor.fetchall():
            buffer.append(row)

        # 执行删除操作和插入操作
        print('EXECUTE:', del_sql, '...')
        rows_count = cursor.execute(del_sql)
        print("Deleted %d rows" % rows_count)

        print('EXECUTE:', inst_sql)

        buffer_100 = []
        insert_rows = 0

        for row in buffer:
            buffer_100.append(row)
            if len(buffer_100) >= 100:
                ignore_count = bulk_execute(cursor, inst_sql, buffer_100)
                insert_rows += len(buffer_100)
                insert_rows -= ignore_count
                buffer_100 = []

        if buffer_100:
            ignore_count = bulk_execute(cursor, inst_sql, buffer_100)
            insert_rows += len(buffer_100)
            insert_rows -= ignore_count

        conn.commit()
        print("Inserted %d rows" % insert_rows)
        return rows_count, insert_rows

    except Exception, e:
        conn.rollback()
        log("CompressError:", e)
        raise

    finally:
        conn.close()


class Command(BaseCommand):
    help = help
    option_list = BaseCommand.option_list + (
        make_option(
            '--db',
            action='store',
            dest='db',
            type='int',
            help='数据库id'),

        make_option(
            '--table',
            action='store',
            dest='table',
            help='表名',
        ),
        make_option(
            '--compress',
            action='store',
            dest='compress',
            help='压缩字段',
        ),

        make_option(
            '--date',
            action='store',
            dest='date',
            type='string',
            help='压缩某一天的数据格式YYYY-MM-DD'),

        make_option(
            '--dt',
            action='store_true',
            dest='dt',
            default=False,
            help='指定字段是否是datetime类型'),

        make_option(
            '--remain',
            action='store',
            dest='remain',
            help='聚合维度'),

        make_option(
            '--sum',
            action='store',
            dest='sum',
            help="聚合字段(取SUM的字段)",
        ),

        make_option(
            '--job',
            action='store',
            dest='job',
            help="AggregateJob id",
        )
    )

    def run(self):
        for job in AggregateJob.objects.all():
            process_aggregatejob(job.id)



    def handle(self, *args, **options):
        print(options)
        try:
            if options['job']:
                jobid = options['job']
                process_aggregatejob(jobid)

                return

            if options['db']:

                if not options['table']:
                    raise CommandError("需要指定表名字，--table TABLENAME")

                if not options['compress']:
                    raise CommandError("需要指定需要压缩的字段")

                if not options['date'] and not options['datetime']:
                    raise CommandError("需要指定压缩日期")

                if not Database.objects.filter(id=options['db']).exists():
                    raise CommandError("类型错误")

                db = Database.objects.get(id=options['db'])
                table = options['table']
                compress = options['compress'].replace(" ", "").split(',')
                if len(compress) > 2:
                    raise CommandError("时间字段设置错误")
                _date = options['date']

                remains_field_list = []
                sum_field_list = []

                if options['remain']:
                    remains_field_list = options['remain'].replace(" ", "").split(',')

                if options['sum']:
                    sum_field_list = options['sum'].replace(" ", "").split(',')

                is_dt = options['dt']

                compress_table(db, table, compress, _date, remains_field_list, sum_field_list, is_dt)
                return

            self.run()

        except CommandError, e:
            log("CommandError:", e)
            raise
