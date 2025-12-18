from .generator import register
from .generator.types import boolean, float, integer, string

register(integer)
register(float)
register(boolean)
register(string)
