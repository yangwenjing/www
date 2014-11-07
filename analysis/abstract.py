# coding: utf8
from collections import defaultdict, namedtuple
from datetime import date, datetime, timedelta
from decimal import InvalidOperation
import re
import urlparse
import MySQLdb
from django.utils import six


Range = namedtuple('Range', ['start', 'end'])


class Dimension(object):
    """
    维度: 此类可以定义一个维度，包括该维度代表数据库中的哪个字段，
    显示名称，怎么清理数据库中的值。
    >>> Dimension('日期', 'date', 'date')
    日期
    """
    def __init__(self, verbose_name, type='char', data_source=None, choices=None):
        assert type in ['date', 'char', 'datetime', 'time', 'province']

        self.verbose_name = verbose_name
        self.type = type
        self.data_source = data_source
        self.choices = choices

        if self.choices:
            self._value_to_display = dict(choices)

    def __unicode__(self):
        return self.verbose_name

    def clean(self, value):
        """
        将数据库中的值转换为要显示的值
        """
        if self.choices:
            return self._value_to_display.get(value)

        if hasattr(self, 'get_display'):
            return self.get_display(value)

        return value

    def normalize(self, value):
        """
        将显示的值转换为数据库中真正的值
        """
        if self.choices:
            for _value, display in self.choices:
                if display == value:
                    return _value

        if self.type in ['date', 'datetime']:
            #将 YYYY-MM-DD 转换为 ``datetime.date``
            if '$' in value:
                if 'thisMonth' in value:
                    value = '$-%d~$0' % (date.today().day - 1)
                elif 'lastMonth' in value:
                    today = date.today()
                    d = today - timedelta(days=today.day)
                    value = '$-%d~$-%d' % (today.day, d.day)

                intlist = [int(i[1:]) for i in value.split('~')]
                print(intlist)
                return [date.today() + timedelta(i) for i in intlist]

            if '~' in value:
                return [date(*[int(i) for i in v.split('-')]) for v in value.split('~')]

            return date(*[int(i) for i in value.split('-')])

        return value

    def group_expr(self):
        if self.type == 'datetime':
            return "date(`%s`)" % self.data_source
        return "`%s`" % self.data_source


class AbstractDimension(Dimension):
    pass


class Property(object):
    """
    数据：此类定义了一个数据，
    描述该数据依赖数据库中的哪些字段，怎么聚合该字段
    """
    def __init__(self, verbose_name, type='number', data_sources=None,
                 clean=None, format=None, unit=''):

        assert type in ['number', 'time', 'size', 'speed', 'percent']

        self.verbose_name = verbose_name
        self.data_sources = data_sources

        if not hasattr(self, 'clean_method'):
            self.clean_method = clean

        if clean:
            self.clean_method = clean

        self.format = format
        self.unit = unit

        if type:
            self.type = type
            if type == 'percent':
                self.format = self.format or '.6f'
                self.unit = self.unit or '%'

    def __unicode__(self):
        return self.verbose_name + " (%s)" % self.unit if self.unit else self.verbose_name

    def aggregate(self):
        return ['SUM(`%s`)' % field for field in self.data_sources]

    def clean(self, *values):
        if callable(self.clean_method):
            try:
                val = self.clean_method(*values)
            except (ZeroDivisionError, InvalidOperation):
                return 0

        else:
            val = values[0]

        if self.format:
            return float(('%' + self.format) % val)

        return val


class PercentProperty(Property):
    """
    百分数字段
    """
    type = 'percent'

    def __init__(self, *args, **kwargs):
        super(PercentProperty, self).__init__(*args, **kwargs)

        self.format = '.6f'
        self.unit = '%'

    def clean_method(self, num1, num2):
        return num1 * 100 / num2


class SizeProperty(Property):
    """
    文件大小字段 (字节)
    """
    type = 'size'


class TimeProperty(Property):
    """
    代表一个时间 (秒)
    """
    type = 'time'


class AvgProperty(Property):
    def clean_method(self, total, count):
        return total / count


class DataSource(object):
    def query(self, view, dimensions, properties, filters):
        """
        :param view: `DataView` 实例
        :param dimensions: 要显示的 `Dimension` 列表
        :param properties: 要显示的 `Property` 列表
        :param filters: 过滤器

        :return: QueryResult(iterable, count, limit=None, offset=0):
        """
        raise NotImplementedError("You should override this method to provide data")


class DatabaseSource(DataSource):
    def __init__(self, db_url, table):
        self.db_url = db_url
        self.table = table

    @classmethod
    def filter_expr(cls, dim, value):
        """
        生成 WHERE 表达式, 返回一个 where 子句列表，和参数列表
        @return: ([sql_where_expression], [params])
        """
        _col = dim.data_source

        # datetime 字段的查询，查询某一天时需要转换成
        if dim.type == 'datetime':
            if isinstance(value, datetime):
                value = value.date()

            # 查询 `datetime` 的字段，却传了一个 `date` 对象，
            # 则转换为当天的范围查询
            if isinstance(value, date):
                start = value
                end = value + timedelta(days=1)

            # 指定了起始日期
            elif isinstance(value, (tuple, list)) and len(value) == 2:
                start = value[0]
                end = value[1] + timedelta(days=1)

            else:
                raise ValueError("Invalid filter on dimension: %s" % dim)

            _df = '%Y-%m-%d'
            _where = " `{0}` >= '{1}' AND `{0}` < '{2}'"
            return [_where.format(_col, start.strftime(_df), end.strftime(_df))], []

        # 优化日期字段的范围查询, 转换成等价的 IN 查询
        elif dim.type == 'date' and isinstance(value, (tuple, set, list)):
            start, end = value
            day_list = [start]
            for x in range((end - start).days):
                day_list.append(start + timedelta(days=x + 1))

            if len(day_list) == 1:
                value = start
            else:
                value = day_list

        # 生成 in 查询
        if isinstance(value, (tuple, list, set)):
            in_list = ['%d' % v if isinstance(v, int) else '"%s"' % v for v in value]
            return ["`%s` in (%s)" % (_col, ', '.join(in_list))], []

        # if isinstance(value, (int, float, Decimal)) or value.isdigit():
        #     return ["`{0}` = %s".format(_col)], [value]

        else:
            return ["`{0}` = %s".format(_col)], [value]

    @classmethod
    def group_expr(cls, dim):
        return dim.group_expr()
        # if isinstance(dim, DateDimension):
        #     return 'date(`%s`)' % dim.data_source
        # return '`%s`' % dim.data_source

    def _build_sql(self, dimensions, properties, filters):
        """生成查询 SQL  """
        sql = """SELECT {dimensions}, {properties} FROM `{table}`
        {where}
        GROUP BY {group_dimensions}"""

        fields = []
        [fields.extend(p.aggregate()) for p in properties]

        fields = list(set(fields))

        sql_result_index = defaultdict(list)

        for p in properties:
            for field in p.aggregate():
                sql_result_index[p].append(fields.index(field))

        # 去掉重复的 GROUP BY (虚拟维度会重复)，且要保持原有的顺序
        dimension_fields = []
        for d in dimensions:
            group_by = DatabaseSource.group_expr(d)
            if not group_by in dimension_fields:
                dimension_fields.append(group_by)

        context = {
            'table': self.table,
            'dimensions': ', '.join(d.group_expr() for d in dimensions),
            'group_dimensions': ', '.join(dimension_fields),
            'properties': ', '.join([f for f in fields]),
            'where': '',
        }

        params = []
        if filters:
            wheres = []
            for k, v in filters.items():
                _ws, _ps = DatabaseSource.filter_expr(k, v)
                wheres.extend(_ws)
                params.extend(_ps)

            context['where'] = 'WHERE ' + ' AND '.join(wheres)

        sql = sql.format(**context)
        self._property_index = sql_result_index
        return sql, params

    def count(self, dimensions, properties, filters):
        sql, params = self._build_sql(dimensions, properties, filters)
        sql = re.sub(r'SELECT .* FROM', 'SELECT COUNT(*) FROM (SELECT 1 FROM', sql) + ') t'
        connection = self.connect()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        print "Execute Count:", cursor._executed
        rs = cursor.fetchone()
        return rs[0]

    def connect(self):
        urlparse.uses_netloc.append('mysql')
        url = urlparse.urlparse(self.db_url)

        return MySQLdb.connect(
            host=url.hostname, port=url.port, db=url.path[1:],
            user=url.username, passwd=url.password,
            charset='utf8')

    def query(self, view, dimensions, properties, filters, limit=None, offset=None):
        sql, params = self._build_sql(dimensions, properties, filters)
        connection = self.connect()
        cursor = connection.cursor()

        if hasattr(view, 'map_all') and callable(view.map_all):
            limit = offset = None

        if limit:
            sql += " LIMIT %s " % limit
        if offset:
            sql += " OFFSET %s " % offset

        cursor.execute('SET NAMES UTF8')
        _rows = cursor.execute(sql, params)
        print "Execute:", cursor._executed

        if offset or (limit and limit == _rows):
            _count = lambda: self.count(dimensions, properties, filters)
        else:
            _count = _rows

        iterator = cursor
        if hasattr(view, 'map_all') and callable(view.map_all):
            iterator = view.map_all(cursor, dimensions, properties)
            if hasattr(iterator, '__len__'):
                _count = len(iterator)

        return QueryResult(self.clean(iterator, dimensions, properties), _count,
                           limit=limit, offset=offset)

    def clean(self, iterator, dimensions, properties):
        _dim_len = len(dimensions)
        sql_result_index = self._property_index

        # 清洗数据：将数据库中的原始值按照 Dimension、Property 的规则清理
        for row in iterator:
            # 清洗维度字段的值
            # 虚拟维度已经在 map_all 中清理过，不需要再次清理
            result = [d.clean(row[i]) if not isinstance(d, AbstractDimension) else row[i]
                      for i, d in enumerate(dimensions)]

            # 清洗数据字段的值
            result.extend(
                prop.clean(*(row[i + _dim_len] for i in sql_result_index[prop]))
                for prop in properties
            )
            yield result


class QueryResult(object):
    def __init__(self, iterable, count, limit=None, offset=0):
        self._iter = iterable
        self._count = count
        self._result_cache = None
        self._limit = limit
        self._offset = offset

    def count(self):
        return self._count() if callable(self._count) else self._count

    def _fetch_all(self):
        if self._result_cache is None:
            self._result_cache = list(self._iter)

    def __iter__(self):
        self._fetch_all()
        return iter(self._result_cache)

    def __getitem__(self, item):
        if not isinstance(item, (slice,) + six.integer_types):
            raise TypeError

        assert ((not isinstance(item, slice) and (item >= 0))
                or (isinstance(item, slice) and (item.start is None or item.start >= 0)
                    and (item.stop is None or item.stop >= 0))), \
                "Negative indexing is not supported."

        if self._offset:
            item = slice(item.start - self._offset, item.stop - self._offset, item.step)

        self._fetch_all()
        return self._result_cache[item]


class DataView(object):
    """
    数据抽象层，将原始的数据库表格，抽象成维度和数据的集合。
    并且可以随意组合维度并聚合数据。

    ``dimensions`` 是维度
    """
    def __init__(self, name, dimensions, properties, data_source):
        self.name = name
        self.dimensions = dimensions
        self.properties = properties
        self.data_source = data_source

    def __unicode__(self):
        return self.name

    def dimension_names(self):
        return [d.verbose_name for d in self.dimensions]

    def property_names(self):
        return [p.verbose_name for p in self.properties]

    def get_filters(self):
        """
        额外的过滤条件，所有查询都会添加此条件
        RETURN {
            Dimension: value
        }
        """
        return {}

    def query(self, dimension_names, property_names, filters=None, limit=None, offset=0):
        """
        用来查询数据，给出维度和数据，返回组合、聚合后的结果

        @param dimension_names: Dimension 的显示名字
        @param property_names: Property 的显示名字
        @param filters: {`Dimension`: 'Dimension.normalize(过滤值)'}
        """
        dimensions = [d for d in self.dimensions if d.verbose_name in dimension_names]
        properties = [p for p in self.properties if p.verbose_name in property_names]

        _index = dict((d.verbose_name, d) for d in self.dimensions)
        _filters = self.get_filters()
        filters = dict((_index[k], _index[k].normalize(v)) for k, v in filters.items()) if filters else None
        if filters:
            _filters.update(filters)

        return self.data_source.query(self, dimensions, properties, _filters, limit, offset)
