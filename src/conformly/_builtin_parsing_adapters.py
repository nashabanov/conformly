from .parsing import register
from .parsing.adapters import dataclass_adapter

register(dataclass_adapter)
