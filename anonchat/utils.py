# -*- coding: utf-8 -*-

from math import log, ceil
from datetime import timezone, timedelta, datetime
from collections import namedtuple

letters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
timezone = timezone(timedelta(hours=9))
MessageMimic = namedtuple('MessageMimic', ('content', 'author', 'created_at'))
UserMimic = namedtuple('UserMimic', ('name', ))


def random_string(len_:int) -> str:
    return ''.join(__import__('random').choice(letters[10:]) for _ in range(len_))


def base36encode(num:int) -> str:
  return ''.join(reversed([letters[digit] for num in (num,) for _ in range(ceil(log(num,36))) for num, digit in ((num//36,num%36),)]))


def jst(timestamp):
    return timestamp.astimezone(timezone)
    
def get_discord_message_mimicked(content='None',author_name='None',created_at=datetime.now()):
    return MessageMimic(content=content,author=UserMimic(name=author_name),created_at=created_at)
