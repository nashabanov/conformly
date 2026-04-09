from ._internal.parsing.adapters import dataclass
from ._internal.parsing.adapters.registry import register

register(dataclass)

try:
    from ._internal.parsing.adapters import pydantic

    register(pydantic)
except ImportError:
    pass
