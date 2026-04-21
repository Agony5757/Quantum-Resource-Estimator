from typing import Dict, Type


class OperationRegistry:
    """Central registry for all Operation subclasses."""
    _registry: Dict[str, Type] = {}

    @classmethod
    def auto_register(cls, node_cls):
        cls._registry[node_cls.__name__] = node_cls
        return node_cls

    @classmethod
    def register(cls, name: str = None):
        def decorator(node_cls):
            key = name or node_cls.__name__
            cls._registry[key] = node_cls
            return node_cls
        return decorator

    @classmethod
    def get_class(cls, name: str):
        if name not in cls._registry:
            raise ValueError(f"Operation '{name}' not registered")
        return cls._registry[name]

    @classmethod
    def has_class(cls, name: str) -> bool:
        return name in cls._registry

    @classmethod
    def remove_class(cls, name: str):
        if name in cls._registry:
            del cls._registry[name]

    @classmethod
    def all_names(cls):
        return list(cls._registry.keys())


# Backward compat alias
NodeRegistry = OperationRegistry
