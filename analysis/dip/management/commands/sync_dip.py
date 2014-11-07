# coding: utf8
from __future__ import unicode_literals, print_function
import os
from datetime import datetime, timedelta
import json
from multiprocessing import Process
from optparse import make_option
from django.core.mail import mail_admins
from django.core.management import BaseCommand, CommandError
from django.db import transaction, connection
from django.db.models import Max
from django.utils.log import getLogger
from warnings import filterwarnings
from MySQLdb import Warning
from analysis.core.models import Database
from analysis.dip.fetcher import Fetcher
from analysis.dip.models import ImportHistory, Job, JobStatus, ImportStatus

filterwarnings('ignore', category=Warning)
help = u"""同步 DIP 分析任务
USAGE: manage.py sync_dip [--list] [--hourly] [--job ID [YYYYMMDDHH]]

从数据库中遍历所有的 Job，并且导入数据

参数
====

--list: 查看所有任务，将忽略其他所有参数

--hourly: 只导入每小时的任务
--daily: 只导入每天的任务

[--job ID]: 指定要导入的 Job ID，如果没有指定则导入全部 Job 的数据
[YYYYMMDD[HH]] 制定要导入的时间戳，如果没有指定则导入从最近一次到现在的所有数据


同步方法
========

将会每个数据库一个进程, 每个进程中多线程导入表，但防止压力过大每个进程最多三个线程同时导入

"""
logger = getLogger('console')


class NoDataException(Exception):
    pass


def log(*args):
    print("Process %d -" % os.getpid(), *args)


def get_job_ts(time, interval):
    """
    @param time: 要取的结果的日志时间
    @param interval: 任务多久跑一次？ DIP 上面每日的任务，结果是运行时间，每小时跑的任务结果却是日志时间
    """
    if interval == 3600:
        return time.strftime('%Y%m%d%H')

    elif interval == 3600 * 24:
        return (time + timedelta(days=1)).strftime('%Y%m%d')

    else:
        raise ValueError("Invalid interval: %d" % interval)


def get_log_time_from_job_ts(ts_str, interval):
    if interval == 3600:
        return datetime.strptime(ts_str, '%Y%m%d%H')
    elif interval == 3600 * 24:
        return datetime.strptime(ts_str, '%Y%m%d') - timedelta(days=1)


def database_process(db_id):
    pid = os.getpid()

    database = Database.objects.get(id=db_id)
    log('processing database:', database)
    jobs = Job.objects.filter(database=database, status=JobStatus.WAITING)
    for job in jobs:
        log('try to process job:', job)
        process_job(job.id)


def process_job(job_id, job_time_str=None):
    with transaction.atomic():
        job = Job.objects.get(id=job_id)
        # 检测任务是否在运行中
        # 因为在处理任务的过程中可能接下来的其它任务状态已经改变了
        if job.status == JobStatus.RUNNING:
            log('Job:', job, "is already running, abort")
            return

        log('Job:', job, "is running now")
        job.status = JobStatus.RUNNING
        job.save()

    try:
        interval = job.interval

        if not job_time_str:
            # 如果没有提供时间参数则自动取 昨天/上一小时的数据。
            now = datetime.now().replace(minute=0, second=0)
            last_time = now - timedelta(seconds=job.interval)

            # last_time = datetime.strptime(self.get_job_ts(last_time, interval), format)
            result = ImportHistory.objects.filter(job=job).aggregate(Max('timestamp'))

            if result.get('timestamp__max'):
                last_update_date = result['timestamp__max']
                log("%s: last update timestamp %s" % (job, last_update_date))

                last_update_date = get_log_time_from_job_ts(last_update_date, interval)
                log("%s: last update date: %s" % (job, last_update_date))

                delta = last_time - last_update_date
                delta = delta.days * 24 * 3600 + delta.seconds
                times = [last_update_date + timedelta(seconds=interval * i)
                         for i in xrange(1, int(delta / interval) + 1)]

                if not times:
                    log("INFO: %s: already up to date" % job)

                    # job.status = JobStatus.WAITING
                    # job.save()
                    return

            else:
                times = [last_time]

        else:
            if ImportHistory.objects.filter(job=job, timestamp=job_time_str, status=ImportStatus.SUCCESS).exists():
                log("ERROR: %s at %s already imported" % (job, job_time_str))
                # job.status = JobStatus.WAITING
                # job.save()
                return

            times = [get_log_time_from_job_ts(job_time_str, interval)]

        for time in times:
            try:
                ts = get_job_ts(time, interval)
                added, ignored = import_job(job, ts)
                log("Job %s at %s: Imported %d, ignored %d" % (job, ts, added, ignored))

                if added == 0 and ignored >= 0:
                    status = ImportStatus.FAILED

                else:
                    status = ImportStatus.SUCCESS

                ImportHistory.objects.create(
                    job=job,
                    timestamp=ts,
                    import_rows=added,
                    ignore_rows=ignored,
                    status=status,
                )

            except NoDataException:
                continue

    finally:
        job.status = JobStatus.WAITING
        job.save()


def import_job(job, job_time_str):
    """
    根据任务设置导入数据

    :param job:
    :return:
    """
    conn = job.database.connect()
    cursor = conn.cursor()
    cursor.execute('SET NAMES UTF8')

    sql = "INSERT INTO `{table}` ({fields}) VALUES ({values})"
    fields = ['`%s`' % f for f in job.fields_list]
    values = ['%s'] * len(job.fields_list)

    sql = sql.format(table=job.table, fields=', '.join(fields), values=', '.join(values))
    fetcher = Fetcher()

    resp = fetcher.fetch_job_result(job.dip_id, job.dip_alias, job_time_str)
    print(resp.status_code)

    conn.autocommit(False)

    buffers = []
    added_count = ignored_count = 0

    try:
        for line in resp.iter_lines():
            if added_count + ignored_count == 0:
                if line and line[0] == '{':
                    result = json.loads(line)
                    if int(result['code']) != 200:
                        log("ERROR: download failed '%s'" % result['msg'])
                        raise NoDataException()

            values = line.strip(str('\t\r')).split(str('\t'))
            if not len(values) == len(fields):
                ignored_count += 1
                continue

            buffers.append(values)

            if len(buffers) == 100:
                _ignored = bulk_execute(cursor, sql, buffers)
                added_count += len(buffers) - _ignored
                ignored_count += _ignored
                buffers = []

        if buffers:
            _ignored = bulk_execute(cursor, sql, buffers)
            added_count += len(buffers) - _ignored
            ignored_count += _ignored

        conn.commit()
        return added_count, ignored_count

    except Exception, e:
        conn.rollback()
        raise


def bulk_execute(cursor, sql, params):
    """
    Return ignored count
    :param cursor:
    :param sql:
    :param params:
    :return:
    """
    ignore_count = 0
    try:
        cursor.executemany(sql, iter(params))
    except Exception, e:
        for param in params:
            try:
                cursor.execute(sql, param)
            except Exception:
                ignore_count += 1

        if ignore_count == len(params):
            raise e

    return ignore_count


class Command(BaseCommand):
    help = help
    option_list = BaseCommand.option_list + (
        make_option(
            '--job',
            action='store',
            dest='job',
            help='导入 ID 是此值的任务, 运行 `sync_dip --list` 查看任务 ID'),

        make_option(
            '--list',
            action='store_true',
            dest='list',
            default=False,
            help='列出所有任务但不运行'
        ),

        make_option(
            '--daily',
            action='store_const',
            const=24 * 3600,
            dest='interval',
            help='只列出每天运行的任务'
        ),

        make_option(
            '--hourly',
            action='store_const',
            const=3600,
            dest='interval',
            help='只列出所有每小时运行的任务'
        ),
    )

    def run(self):
        dbs = Database.objects.filter(id__in=Job.objects.values('database').distinct())
        dbs = list(dbs)
        # close connection to avoid new process
        # started by multiprocess reuse this connection
        connection.close()

        for db in dbs:
            Process(target=database_process, args=(db.id, )).run()

    def handle(self, *args, **options):
        # format = '%Y%m%d%H' if interval == 3600 else '%Y%m%d'
        if options['list']:
            interval = options['interval']

            if interval:
                jobs = Job.objects.filter(interval=interval)
            else:
                jobs = Job.objects.all()

            for job in jobs:
                log('#%-4d %-6s %s' % (job.id, job.get_interval_display(), job.table))

                if options['verbosity'] == '2':
                    log('Fields: %s' % job.fields)
                    log("Dip   : %-15s %-30s \n" % (job.dip_id, job.dip_alias))
                continue

            return

        if options['job']:
            if not options['job'].isdigit():
                raise CommandError('Job ID 必须为数字')

            try:
                job = Job.objects.get(id=options['job'])
                if job.status == JobStatus.RUNNING:
                    raise CommandError('另外一个进程正在导入该任务')

                time_str = args[0] if args else None
                process_job(job.id, time_str)
                return

            except Job.DoesNotExist:
                raise CommandError('Job 不存在')

        # param_time = datetime.strptime(args[0], format) if args else None
        self.run()
