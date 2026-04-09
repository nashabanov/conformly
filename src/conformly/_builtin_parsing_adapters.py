from ._internal.parser.adapters import dataclass
from ._internal.parser.adapters.registry import register

register(dataclass)

try:
    from ._internal.parser.adapters import pydantic

    register(pydantic)
except ImportError:
    pass
