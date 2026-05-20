def register_builtin_adapters() -> None:
    from . import dataclass, typeddict
    from .registry import register

    register(dataclass)
    register(typeddict)

    try:
        from . import pydantic
    except ImportError:
        return

    register(pydantic)
