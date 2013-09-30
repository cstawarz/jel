from __future__ import division, print_function, unicode_literals
import fileinput

from . import parse


src = ''.join(line for line in fileinput.input())
root = parse(src)
if root:
    print(root)
