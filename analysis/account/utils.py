# coding: utf8
from __future__ import unicode_literals


def in_group(user, group):
    """
    判断用户是否在一个组中
    :param user: `User`
    :param group: `Group`
    :return: boolean
    """
    return user.groups.filter(id=group.id).exists()
