def register_builtin_adapters() -> None:
    from . import dataclass
    from .registry import register

    register(dataclass)

    try:
        from . import pydantic
    except ImportError:
        return

    register(pydantic)
