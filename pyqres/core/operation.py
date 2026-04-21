from typing import Dict, List, Tuple, Union

from .registry import OperationRegistry
from .metadata import RegisterMetadata, program_metadata
from .utils import merge_controllers, controller2str, reg_sz


class OperationMeta(type):
    """Metaclass that auto-registers all concrete Operation subclasses."""
    def __new__(cls, name, bases, namespace):
        new_class = super().__new__(cls, name, bases, namespace)
        if not namespace.get('__abstract__', False):
            OperationRegistry.auto_register(new_class)
        return new_class


class Operation(metaclass=OperationMeta):
    """Base class for all quantum operations.

    Two concrete subclasses:
    - Primitive: leaf node with known resource cost (T-count, etc.)
    - Composite: decomposes into sub-operations via program_list
    """
    __abstract__ = True
    __self_conjugate__ = False  # Default: operation changes under dagger

    def __init__(self, reg_list=None, param_list=None, temp_reg_list=None,
                 submodules=None, **kwargs):
        self.program_list: List['Operation'] = []
        self.reg_list: list = reg_list or []
        self.param_list: list = param_list or []
        self.temp_reg_list: list = temp_reg_list or []
        self.submodules: list = submodules or []
        self.dagger_flag = False
        self.controllers: Dict = {}
        self.name = self.__class__.__name__

        if not kwargs.get("no_declare", False):
            self.declare_qfunction()

    @staticmethod
    def program_type():
        return "Operation"

    def declare_qfunction(self):
        program_metadata.declare_qfunction(
            self.name,
            len(self.reg_list),
            len(self.param_list),
            len(self.temp_reg_list),
            len(self.submodules))

    def declare_program_list(self):
        program_metadata.declare_program_list(self.name, program_list=self.program_list)

    def validate_registers(self):
        register_metadata_ = RegisterMetadata.get_register_metadata()
        for reg in self.reg_list:
            if reg not in register_metadata_.registers:
                raise ValueError(f"Register {reg} not declared")

    # ── Controller chain ──

    def control(self, controller):
        if isinstance(controller, (list, str)):
            return self.control_by_all_ones(controller)
        if isinstance(controller, dict):
            self.controllers = merge_controllers(self.controllers, controller)
        return self

    def control_by_all_ones(self, controller):
        if "conditioned_by_all_ones" not in self.controllers:
            self.controllers["conditioned_by_all_ones"] = []
        if isinstance(controller, list):
            self.controllers["conditioned_by_all_ones"].extend(controller)
        else:
            self.controllers["conditioned_by_all_ones"].append(controller)
        return self

    def control_by_nonzero(self, controller):
        if "conditioned_by_nonzero" not in self.controllers:
            self.controllers["conditioned_by_nonzero"] = []
        if isinstance(controller, list):
            self.controllers["conditioned_by_nonzero"].extend(controller)
        else:
            self.controllers["conditioned_by_nonzero"].append(controller)
        return self

    def control_by_bit(self, controller):
        if "conditioned_by_bit" not in self.controllers:
            self.controllers["conditioned_by_bit"] = []
        if isinstance(controller, list):
            self.controllers["conditioned_by_bit"].extend(controller)
        else:
            self.controllers["conditioned_by_bit"].append(controller)
        return self

    def control_by_value(self, controller):
        if "conditioned_by_value" not in self.controllers:
            self.controllers["conditioned_by_value"] = []
        if isinstance(controller, list):
            self.controllers["conditioned_by_value"].extend(controller)
        else:
            self.controllers["conditioned_by_value"].append(controller)
        return self

    def dagger(self):
        self.dagger_flag = not self.dagger_flag
        return self

    def is_self_conjugate(self) -> bool:
        """Check if operation is self-conjugate (U† = U).

        Self-conjugate operations don't change when dagger is applied.
        This affects T-count, T-depth, simulation, and operation unrolling.
        """
        return getattr(self.__class__, '__self_conjugate__', False)

    # ── Rendering ──

    def render_parameters(self):
        return ", ".join(str(p) for p in self.param_list)

    def render_registers(self):
        register_metadata_ = RegisterMetadata.get_register_metadata()
        return ", ".join(
            f"{reg}" + (f"[{register_metadata_.registers[reg]}]"
                        if register_metadata_.registers.get(reg) is not None else "")
            for reg in self.reg_list)

    def render_submodules(self):
        return ", ".join(f"{sm.__name__}" for sm in self.submodules)

    def render_this(self, indent=0, dagger_ctx=False, controllers_ctx=None):
        return self.plain_render_this(indent, dagger_ctx, controllers_ctx)

    def plain_render_this(self, indent=0, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        reg_str = self.render_registers()
        ret = f"{' ' * indent}{self.name}"
        dagger_ctx = self.dagger_flag ^ dagger_ctx
        controllers_ctx = merge_controllers(self.controllers, controllers_ctx)
        if dagger_ctx:
            ret += ".dag"
        ret += f": QRegs({reg_str})"
        if self.param_list:
            ret += f", Params({self.render_parameters()})"
        if self.submodules:
            ret += f", Submodules({self.render_submodules()})"
        if controllers_ctx:
            ret += f", Controllers({controller2str(controllers_ctx)})"
        return ret

    def __repr__(self):
        from .visitor import tree_renderer
        tree_renderer.text = ""
        self.traverse(tree_renderer)
        return tree_renderer.text

    def __str__(self):
        from .visitor import plain_renderer
        plain_renderer.text = ""
        self.traverse(plain_renderer)
        return plain_renderer.text

    # ── T-count ──

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            f"{self.__class__.__name__} must override t_count()")

    def sum_t_count(self, t_count_list):
        return sum(t_count_list)

    # ── T-depth ──

    def t_depth(self, current_t_depth, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            f"{self.__class__.__name__} must override t_depth()")

    def merge_t_depth(self, current_t_depth, t_depth_list):
        from .visitor import forward_t_depth
        for t_depth in t_depth_list:
            current_t_depth = forward_t_depth(current_t_depth, t_depth)
        return current_t_depth

    # ── Toffoli-count ──

    def toffoli_count(self, dagger_ctx=False, controllers_ctx=None):
        raise NotImplementedError(
            f"{self.__class__.__name__} must override toffoli_count()")

    def sum_toffoli_count(self, toffoli_count_list):
        return sum(toffoli_count_list)

    # ── Traversal ──

    def enter(self, dagger_ctx=False, controllers_ctx=None):
        RegisterMetadata.add_registers(self.temp_reg_list)

    def exit(self, dagger_ctx=False, controllers_ctx=None):
        RegisterMetadata.remove_registers(
            reg for reg, size in self.temp_reg_list)

    def traverse(self, visitor, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        self.enter(dagger_ctx, controllers_ctx)
        self.validate_registers()
        visitor.enter(self)
        visitor.visit(self, dagger_ctx, controllers_ctx)
        self.traverse_children(visitor, dagger_ctx, controllers_ctx)
        visitor.exit(self)
        self.exit(dagger_ctx, controllers_ctx)

    def traverse_children(self, visitor, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        # Compute effective dagger: XOR with dagger_flag, but if self_conjugate, stop propagation
        effective_dagger = self.dagger_flag ^ dagger_ctx
        if self.is_self_conjugate():
            effective_dagger = False  # Self-conjugate: dagger has no effect

        controllers_ctx = merge_controllers(controllers_ctx, self.controllers)
        if effective_dagger:
            for program in reversed(self.program_list):
                program.traverse(visitor, dagger_ctx=effective_dagger,
                                 controllers_ctx=controllers_ctx)
        else:
            for program in self.program_list:
                program.traverse(visitor, dagger_ctx=effective_dagger,
                                 controllers_ctx=controllers_ctx)


class Primitive(Operation):
    """Leaf operation with known resource cost. Cannot be further decomposed."""
    __abstract__ = True

    @staticmethod
    def program_type():
        return "Primitive"

    def traverse_children(self, visitor, dagger_ctx=False, controllers_ctx=None):
        pass  # Primitives have no children

    def t_depth(self, current_t_depth, dagger_ctx=False, controllers_ctx=None):
        """Default T-depth implementation: adds t_count to all involved registers."""
        from .visitor import sync_t_depth
        t = self.t_count(dagger_ctx, controllers_ctx)
        if t is None:
            return
        # Get all registers involved in this operation
        regs = list(self.reg_list)
        # Sync all registers to the same depth
        sync_t_depth(current_t_depth, regs)
        # Add t_count as T-depth contribution
        for reg in regs:
            current_t_depth[reg] = current_t_depth.get(reg, 0) + t

    def toffoli_count(self, dagger_ctx=False, controllers_ctx=None):
        """Default Toffoli-count: approximated as t_count / 7."""
        t = self.t_count(dagger_ctx, controllers_ctx)
        if t is None:
            return None
        return t // 7


class Composite(Operation):
    """Operation that decomposes into sub-operations via program_list."""
    __abstract__ = True

    @staticmethod
    def program_type():
        return "Composite"

    def t_count(self, dagger_ctx=False, controllers_ctx=None):
        return None  # Has children; sum via visitor

    def t_depth(self, current_t_depth, dagger_ctx=False, controllers_ctx=None):
        return None  # Has children; merge via visitor

    def toffoli_count(self, dagger_ctx=False, controllers_ctx=None):
        return None  # Has children; sum via visitor


class StandardComposite(Composite):
    """Composite with default summation: sum children's T-counts."""
    __abstract__ = True


class AbstractComposite(Composite):
    """Composite with custom sum_t_count() aggregation."""
    __abstract__ = True

    def sum_t_count(self, t_count_list):
        raise NotImplementedError(
            f"{self.__class__.__name__} must override sum_t_count()")


def mock_submodule(name):
    """Create a mock Operation subclass for type signatures."""
    def __general_mock_init(self, reg_list=None, param_list=None,
                            temp_reg_list=None, submodules=None):
        Operation.__init__(self,
                          reg_list=reg_list or [],
                          param_list=param_list or [],
                          temp_reg_list=temp_reg_list or [],
                          submodules=submodules or [],
                          no_declare=True)
    cls_ = type(name, (Operation,), {"__init__": __general_mock_init})
    OperationRegistry.remove_class(cls_)
    return cls_
