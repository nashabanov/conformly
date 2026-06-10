def register_builtin_adapters() -> None:
    from . import dataclass, typeddict
    from .registry import register

    register(dataclass)
    register(typeddict)

    try:
        from . import pydantic
    except ImportError:
        pass
    else:
        register(pydantic)

    try:
        from . import attrs
    except ImportError:
        pass
    else:
        register(attrs)
