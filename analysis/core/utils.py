# coding: utf8
from __future__ import unicode_literals
import time
from datetime import date, datetime, time as datetime_time
import json
from decimal import Decimal
from django.http import HttpResponse
import sys


def render_json(obj):
    def default(obj):
        if isinstance(obj, datetime_time):
            return obj.strftime("%H:%M")

        elif isinstance(obj, (datetime, date)):
            return int(time.mktime(obj.timetuple()))

        elif isinstance(obj, Decimal):
            return float('%.2f' % obj)

    return HttpResponse(json.dumps(obj, default=default), mimetype='application/json')


def inline_map(function, row, _slice):
    """在水平方向上进行 map
    >>> inline_map(lambda x: x +1, ['a', 'b', 1, 2, 3], slice(2:))
    ['a', 'b', 2, 3, 4]
    """
    if not isinstance(_slice, slice):
        raise TypeError("slice 必须为 slice 对象")

    if _slice.step:
        raise ValueError("slice 不支持 step")

    stop = _slice.stop if not _slice.stop is None else sys.maxint
    start = _slice.start if not _slice.start is None else 0
    return [function(v) if start <= idx < stop else v for idx, v in enumerate(row)]
