from __future__ import division, print_function, unicode_literals
import fileinput

from . import parse
from .compiler import Compiler


src = ''.join(line for line in fileinput.input())
root = parse(src)
if root:
    ops = Compiler().compile(root)
    Compiler.print_ops(ops)
