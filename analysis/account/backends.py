import urllib2
import json
import urllib
from django.contrib.auth.models import User


class LdapBackend(object):
    def __init__(self, args=None):
        self.postfix = '@staff.sina.com.cn'

    def authenticate(self, username=None, password=None):
        user_pwd_valid = self.staff_auth(username, password)

        if user_pwd_valid:
            username = username.split('@')[0]
            try:
                user = User.objects.get(username=username)

            except User.DoesNotExist:
                user = User(username=username, email=username + self.postfix)
                user.set_unusable_password()
                user.save()

            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def staff_auth(self, username='', password=''):
        if not username or not password:
            return False

        username = username.split('@')
        if len(username) > 2:
            return False
        if len(username) == 2 and username[1] != self.postfix:
            return False

        data = {'user': '%s%s' % (username[0], self.postfix), 'pw': password}
        data = urllib.urlencode(data)

        url = 'http://10.75.6.48/go/api/idle_auth.php'
        req = urllib2.Request(url)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, data)
        response_json = json.load(response)

        if response_json.get('msg') == 'success':
            return True

        return False



