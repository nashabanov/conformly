from .parsing import register
from .parsing.adapters import dataclass

register(dataclass)

try:
    from .parsing.adapters import pydantic

    register(pydantic)
except ImportError:
    pass
