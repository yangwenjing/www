# coding: utf8
from __future__ import unicode_literals, division
import csv
from itertools import groupby
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
import math
from datetime import datetime, timedelta, time
from django.shortcuts import render
import string

from analysis.core.utils import render_json, inline_map


def key_hash(obj):
    if isinstance(obj, str):
        return obj.decode('utf8')
    else:
        return unicode(obj)


def variance(iterator, dimensions, properties):
    dim_len = len(dimensions)
    prop_len = len(properties)

    # 将所有纬度都一样的值分组
    group_key = lambda row: u'-'.join(
        key_hash(value) if idx else 'date' for idx, value in enumerate(row[:dim_len])
    )

    _variance = lambda value, avg: (value - avg) ** 2
    results = []
    for key, rows_iter in groupby(sorted(iterator, key=group_key), key=group_key):
        # 为每行添加方差的列
        rows = [row + [0] * prop_len for row in rows_iter]
        sums = reduce(
            lambda row1, row2: (
                row1[:dim_len] +
                [row1[dim_len + i] + row2[dim_len + i] for i in xrange(prop_len)] +
                row1[dim_len + prop_len:]
            ),
            rows
        )
        print 'rows', key, rows
        print 'sums', key, len(rows), sums[dim_len:dim_len + prop_len]

        rows_len = len(rows)
        avgs = inline_map(lambda x: x / rows_len, sums, slice(dim_len, dim_len + prop_len))
        print 'avgs', key, avgs

        v_idx = dim_len + prop_len

        row = reduce(
            lambda row1, row2: (
                row2[:dim_len] +
                [avgs[dim_len + i] for i in xrange(prop_len)] +
                [row1[v_idx + i] + _variance(row2[dim_len + i], avgs[dim_len + i]) for i in xrange(prop_len)]
            ),
            rows,
            [0] * (dim_len + prop_len * 2)
        )

        try:
            for x in xrange(prop_len):
                row[v_idx + x] = Decimal(str(math.sqrt(row[v_idx + x] / rows_len))) / Decimal(str(avgs[dim_len + x]))
                row[v_idx + x] = round(float(row[v_idx + x]), 2)
        except InvalidOperation:
            continue

        print 'reduced', key, row
        results.append(row)

    return results


def report(request, view):
    dimension_names = request.REQUEST.getlist('d') or view.dimension_names()[:2]
    property_names = request.REQUEST.getlist('p') or view.property_names()[:4]

    for _list in [dimension_names, property_names]:
        for idx, d in enumerate(_list):
            if d.split(','):
                del _list[idx]
                _list.extend((_d for _d in d.split(',') if _d.strip()))

    # 支持维度过滤多个值
    _q = request.GET
    filters = {}
    for dim in view.dimensions:
        if dim.verbose_name in _q:
            values = _q.getlist(dim.verbose_name)
            if len(values) == 1:
                filters[dim.verbose_name] = values[0]
            else:
                filters[dim.verbose_name] = values

    selected_dimensions = [d for d in view.dimensions if d.verbose_name in dimension_names]
    selected_properties = [p for p in view.properties if p.verbose_name in property_names]

    page = request.GET.get('page', '')
    page = int(page) if page.isdigit() else 1
    limit = int(request.GET.get('limit') or '100')

    start_date = end_date = None

    # 给时间字段添加一个默认过滤器
    for d in view.dimensions:
        if d.type in ['date', 'datetime']:
            if not d.verbose_name in filters:
                filters[d.verbose_name] = datetime.now().date().strftime('%Y-%m-%d')
                start_date = end_date = datetime.now().date()

            else:
                filter_value = filters[d.verbose_name]
                if '~' in filter_value:
                    start_date, end_date = d.normalize(filter_value)
                else:
                    start_date = end_date = d.normalize(filter_value)

    if request.GET.get('export') == 'csv':
        resp = HttpResponse(mimetype='text/csv')
        # resp['Content-Disposition'] = 'attachment; filename=table.csv'
        writer = csv.writer(resp)

        rows = view.query(dimension_names, property_names, filters)
        writer.writerow([header.verbose_name.encode('utf8') for header in selected_dimensions + selected_properties])
        for row in rows:
            writer.writerow([r.encode('utf8') if isinstance(r, unicode) else r for r in row])

        return resp

    if '$variance' in request.GET:
        rows = variance(view.query(dimension_names, property_names, filters, offset=0),
                        selected_dimensions,
                        selected_properties)

    else:
        rows = view.query(dimension_names, property_names, filters, limit=limit, offset=(page - 1) * limit)

    # 获取percent在property中的位置
    dim_types = [d.type for d in selected_dimensions]
    p_types = [p.type for p in selected_properties]
    percent_position = []

    while 'percent' in p_types:
        percent_index = p_types.index('percent')
        percent_position.append(percent_index)
        p_types[percent_index] = '%'

    if request.is_ajax():
        rows = view.query(dimension_names, property_names, filters)


        columns = [{'type': 'dimension', 'name': d.verbose_name, 'data_type': d.type} for d in selected_dimensions]
        columns += [{'type': 'property', 'name': p.verbose_name, 'data_type': p.type} for p in selected_properties]

        results = []
        # 合并 Date 和 Time
        if 'date' in dim_types and 'time' in dim_types:
            date_index = dim_types.index('date')
            time_index = dim_types.index('time')
            #在这里处理百分比的显示

            del columns[time_index]
            del dim_types[time_index]


            for row in rows:
                _date, _time = row[date_index], row[time_index]
                if isinstance(_time, timedelta):
                    row[date_index] = datetime.combine(_date, time.min) + _time
                else:
                    row[date_index] = datetime.combine(_date, _time)

                del row[time_index]
                results.append(row)

        else:
            results = list(rows)

        if percent_position:
            for row in results:
                for position in percent_position:
                    num = string.atof(row[len(dim_types)+position])*100
                    row[len(dim_types)+position] = '%.3f' % num + '%'

        return render_json({
            'columns': columns,
            'rows': results
        })

    # 将 filters 里面的 Dimension 的名字转换为 Dimension 实例
    filters_items = ((d, filters[d.verbose_name]) for d in view.dimensions if d.verbose_name in filters)
    if percent_position:
            for row in rows:
                for position in percent_position:
                    num = string.atof(row[len(dim_types)+position])*100
                    row[len(dim_types)+position] = '%.3f' % num + '%'
    context = {
        'dimensions': selected_dimensions,
        'properties': selected_properties,
        'filters': filters_items,
        'view': view,
        'result': rows,
        'start_date': start_date,
        'end_date': end_date,
        'variance': '$variance' in request.GET,
        'limit': limit,
    }

    return render(request, "dashboard/report.html", context)
