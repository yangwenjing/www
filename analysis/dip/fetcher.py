#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
import urllib
import json
import time
import hmac
import hashlib
import requests


class Fetcher(object):
    """
    从综合运维平台获取数据
    """
    PRODUCT = "新浪内容加速平台"
    ACCESSKEY = "YxsiOT61334888974480"
    SECRETKEY = "93f16098ca0f45d7b149616b48d95141ORqxoyhp"
    INTERFACE = "http://api.dip.sina.com.cn"

    def fetch_url(self, url, timeout=20):
        resp = requests.get(url, timeout=timeout)
        httpcode = resp.status_code

        if httpcode in [0, 500]:
            raise Exception("500接口调用错误")

        return resp

    def fetch_data(self, url, timeout=20):
        response_content = self.fetch_url(url, timeout=timeout)
        try:
            content_json_decode = json.loads(response_content)
        except Exception as err:
            raise Exception("json decode err: %s" % str(err))

        retcode = content_json_decode.get('code', None)
        if retcode is None:
            raise Exception('return format error, no errno key')

        if int(retcode) == 0:
            return content_json_decode['data']

        elif int(retcode) == 40001:
            raise Exception("无带宽数据")

        raise Exception("%s" % content_json_decode['msg'])

    def dip_ssig(self, qs, uri, timestamp):
        if qs:
            pattern = "GET\n\n\n\n{uri}?{sorted_qs}&accesskey={accesskey}&timestamp={timestamp}"
        else:
            pattern = "GET\n\n\n\n{uri}?accesskey={accesskey}&timestamp={timestamp}"

        string_to_sign = pattern.format(
            uri=uri,
            sorted_qs='&'.join(['%s=%s' % (k, qs[k]) for k in sorted(qs)]),
            accesskey=self.ACCESSKEY,
            timestamp=timestamp,
        )
        return hmac.new(str(self.SECRETKEY), str(string_to_sign), hashlib.sha1).digest().encode('base64')[5:15]

    def fetch_job_result(self, jobid, aliasname, day_str):
        """
        http://api.dip.sina.com.cn/rest/v2/file/download_by_aliasname/{jobid}/{aliasname}?accesskey=&timestamp=&ssig=
        """
        #day_str = day.strftime('%Y%m%d')
        uri = "/rest/v2/file/download_by_aliasname_new/%s/%s_%s" % (jobid, aliasname, day_str)

        # qs 仅初始化业务参数, 计算 ssig 用
        qs = {}
        timestamp = int(time.time())
        ssig = self.dip_ssig(qs, uri, timestamp)

        # 填充所有 url 中将用到的参数
        qs.update({
            'accesskey': self.ACCESSKEY,
            'ssig': urllib.quote_plus(ssig),  # 对 + 和 / 进行 url encode
            'timestamp': timestamp,
        })

        url = "{interface}{uri}?{qs}".format(
            interface=self.INTERFACE,
            uri=urllib.quote(uri),
            qs='&'.join(['%s=%s' % (k, qs[k]) for k in qs]),
        )
        print url
        response_content = self.fetch_url(url, timeout=2000)
        return response_content


if __name__ == "__main__":
    f = Fetcher()
    data = f.fetch_job_result(
        '136566594318511', 'nginx_domain_refer_2XX',
        day_str='20130712')
    for l in data:
        print l
