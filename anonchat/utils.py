# -*- coding: utf-8 -*-

from math import log, ceil
from random import choice

letters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def random_string(len_:int) -> str:
    return ''.join(choice(letters[10:]) for _ in range(len_))


def base36encode(num:int) -> str:
  return ''.join(reversed([letters[digit] for num in (num,) for _ in range(ceil(log(num,36))) for num, digit in ((num//36,num%36),)]))

