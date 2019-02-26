from math import log, ceil

letters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


# random_strings = lambda len_: ''.join(__import__('random').choice(letters) for _ in range(len_))
def random_string(len_):
    return ''.join(__import__('random').choice(letters[10:]) for _ in range(len_))


def base36encode(num):
  return ''.join(reversed([letters[digit] for num in (num,) for _ in range(ceil(log(num,36))) for num, digit in ((num//36,num%36),)]))

