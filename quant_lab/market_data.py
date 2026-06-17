"""`market_data` legacy root 的兼容别名。"""

from importlib import import_module
import sys

_module = import_module("market_data")
sys.modules[__name__] = _module
