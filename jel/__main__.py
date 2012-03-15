from __future__ import division, print_function, unicode_literals
import sys

from . import parse


root = parse(sys.argv[1])
if root:
    print(root)
