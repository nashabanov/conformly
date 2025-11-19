from conformly.generator.protocol import TypeGeneratorProtocol
from conformly.specs import FieldSpec

_generators: list[TypeGeneratorProtocol] = []


def register(generator: TypeGeneratorProtocol) -> None:
    _generators.append(generator)


def get_generator(field: FieldSpec) -> TypeGeneratorProtocol:
    for generator in _generators:
        if generator.supports(field):
            return generator
    raise TypeError(f"No generators found for {field.type}")
