"""
Primitive Registry for Quantum-Resource-Estimator DSL.

Manages primitive sets for lowering decisions. A primitive set defines which
operations are "leaf nodes" (not lowered further). Different sets for different
hardware/simulation targets.
"""

from typing import Dict, Set, Optional, List
from pathlib import Path
import yaml


class PrimitiveRegistryError(Exception):
    """Exception raised for primitive registry errors."""
    pass


class PrimitiveRegistry:
    """
    Manages primitive sets for lowering decisions.

    A primitive set defines which operations are considered "atomic" and
    should not be decomposed further. This allows switching between different
    gate sets (e.g., Clifford+T, Toffoli-based, QRAM-based).

    Example:
        # Load primitive sets
        PrimitiveRegistry.load_primitive_set("clifford_t.primitive.yaml")

        # Set active set
        PrimitiveRegistry.set_active("clifford_t")

        # Check if operation is primitive
        if PrimitiveRegistry.is_primitive("Hadamard"):
            # Don't lower, use native implementation
            pass
    """

    _sets: Dict[str, Set[str]] = {}
    _active_set: Optional[str] = None

    @classmethod
    def reset(cls):
        """Reset all primitive sets and active set."""
        cls._sets = {}
        cls._active_set = None

    @classmethod
    def load_primitive_set(cls, yaml_path: str) -> str:
        """
        Load a primitive set from a .primitive.yaml file.

        Args:
            yaml_path: Path to the primitive set YAML file

        Returns:
            The name of the loaded primitive set

        Raises:
            PrimitiveRegistryError: If the file is invalid
        """
        path = Path(yaml_path)
        if not path.exists():
            raise PrimitiveRegistryError(f"Primitive set file not found: {yaml_path}")

        with open(path) as f:
            definition = yaml.safe_load(f)

        if definition is None:
            raise PrimitiveRegistryError(f"Empty primitive set file: {yaml_path}")

        # Validate required fields
        if "name" not in definition:
            raise PrimitiveRegistryError(f"Missing 'name' in primitive set: {yaml_path}")

        if "primitives" not in definition:
            raise PrimitiveRegistryError(f"Missing 'primitives' in primitive set: {yaml_path}")

        name = definition["name"]
        primitives = set(definition.get("primitives", []))

        if not primitives:
            raise PrimitiveRegistryError(f"Empty primitive set: {name}")

        cls._sets[name] = primitives
        return name

    @classmethod
    def load_from_directory(cls, directory: str) -> List[str]:
        """
        Load all primitive sets from a directory.

        Args:
            directory: Directory containing .primitive.yaml files

        Returns:
            List of loaded primitive set names
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        loaded = []
        for prim_file in dir_path.glob("*.primitive.yaml"):
            try:
                name = cls.load_primitive_set(str(prim_file))
                loaded.append(name)
            except PrimitiveRegistryError:
                pass  # Skip invalid files

        return loaded

    @classmethod
    def set_active(cls, set_name: str):
        """
        Set the active primitive set.

        Args:
            set_name: Name of the primitive set to activate

        Raises:
            PrimitiveRegistryError: If the set is not loaded
        """
        if set_name not in cls._sets:
            available = list(cls._sets.keys())
            raise PrimitiveRegistryError(
                f"Primitive set '{set_name}' not loaded. "
                f"Available sets: {available}"
            )
        cls._active_set = set_name

    @classmethod
    def get_active_set(cls) -> Optional[str]:
        """Get the name of the active primitive set."""
        return cls._active_set

    @classmethod
    def get_active_primitives(cls) -> Set[str]:
        """
        Get the current active primitive set.

        Returns:
            Set of primitive operation names, or empty set if no active set
        """
        if cls._active_set is None:
            return set()  # No primitives - everything needs decomposition
        return cls._sets.get(cls._active_set, set())

    @classmethod
    def is_primitive(cls, operation_name: str) -> bool:
        """
        Check if an operation is in the active primitive set.

        Args:
            operation_name: Name of the operation to check

        Returns:
            True if the operation is a primitive, False otherwise
        """
        return operation_name in cls.get_active_primitives()

    @classmethod
    def validate_operation(cls, operation_name: str, has_decomposition: bool) -> bool:
        """
        Validate that an operation is either a primitive or has a decomposition.

        Args:
            operation_name: Name of the operation to validate
            has_decomposition: Whether the operation has a decomposition (impl)

        Returns:
            True if the operation is valid

        Raises:
            PrimitiveRegistryError: If the operation is neither primitive nor decomposable
        """
        if cls.is_primitive(operation_name):
            return True

        if has_decomposition:
            return True

        raise PrimitiveRegistryError(
            f"Operation '{operation_name}' is not in the active primitive set "
            f"('{cls._active_set}') and has no decomposition defined. "
            f"Either add it to the primitive set or provide an implementation."
        )

    @classmethod
    def list_sets(cls) -> List[str]:
        """List all loaded primitive set names."""
        return list(cls._sets.keys())

    @classmethod
    def get_set_primitives(cls, set_name: str) -> Set[str]:
        """
        Get the primitives in a specific set.

        Args:
            set_name: Name of the primitive set

        Returns:
            Set of primitive operation names

        Raises:
            PrimitiveRegistryError: If the set is not loaded
        """
        if set_name not in cls._sets:
            raise PrimitiveRegistryError(f"Primitive set '{set_name}' not loaded")
        return cls._sets[set_name].copy()
