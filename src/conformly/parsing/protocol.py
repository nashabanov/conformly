from typing import Protocol

from conformly.specs import ModelSpec


class ParcingAdapterProtocol(Protocol):
    """Interface that all parsing adapters must implement"""

    def supports(self, model: type) -> bool:
        """Return True if adapter can parse given model type"""
        ...

    def parse(self, model: type) -> ModelSpec:
        """Return parsed ModelSpec from given model"""
        ...
