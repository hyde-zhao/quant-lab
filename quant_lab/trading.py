"""`trading` legacy root 的兼容别名。"""

from importlib import import_module
import sys

_module = import_module("trading")
sys.modules[__name__] = _module
