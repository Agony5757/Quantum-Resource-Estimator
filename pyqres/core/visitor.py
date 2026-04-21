from typing import Dict, List, Union
from sympy import Symbol
import sympy as sp


# ── T-depth helper functions ──

def get_depth(t_reg_depth_node: Dict[str, Union[int, Symbol]]):
    if not t_reg_depth_node:
        return 0
    values = list(t_reg_depth_node.values())
    if all(isinstance(v, int) for v in values):
        return max(values)
    return sp.Max(*values)


def sync_t_depth(current_depth: Dict[str, Union[int, Symbol]], regs: List[str]):
    if not regs:
        return current_depth
    depths = [current_depth.get(reg, 0) for reg in regs]
    sync_to = max(depths) if all(isinstance(d, int) for d in depths) else sp.Max(*depths)
    current_depth.update({reg: sync_to for reg in regs})
    return current_depth


def forward_t_depth(current_depth: Dict[str, Union[int, Symbol]],
                    t_depth: Dict[str, Union[int, Symbol]]):
    current_depth = sync_t_depth(current_depth, list(t_depth.keys()))
    for reg in t_depth:
        current_depth[reg] += t_depth[reg]
    return current_depth


# ── T-Count Visitor ──

class TCounter:
    """Visitor that computes total T-gate count via lowering."""

    def __init__(self):
        self.count_stack = [[]]

    def enter(self, node):
        self.count_stack.append([])

    def exit(self, node):
        current = self.count_stack.pop()
        total = node.sum_t_count(current)
        self.count_stack[-1].append(total)

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        t_count = node.t_count(dagger_ctx, controllers_ctx)
        if t_count is not None:
            self.count_stack[-1].append(t_count)

    def get_count(self):
        if len(self.count_stack) != 1:
            raise ValueError("Stack is not empty")
        if len(self.count_stack[0]) != 1:
            raise ValueError("Stack top is not a list of length 1")
        return self.count_stack[0][0]


# ── T-Depth Visitor ──

class TDepthCounter:
    """Visitor that computes T-gate depth via lowering."""

    def __init__(self):
        self.traverse_node_type = []
        self.count_stack = []
        self.reg_depth = None

    def enter(self, node):
        self.traverse_node_type.append(node.program_type())
        if node.program_type() in ('AbstractComposite', 'AbstractProgram'):
            self.count_stack.append([])
        else:
            if len(self.traverse_node_type) == 1:
                self.reg_depth = {}
                self.count_stack.append(self.reg_depth)
            elif self.traverse_node_type[-2] in ('AbstractComposite', 'AbstractProgram'):
                self.reg_depth = {}
                self.count_stack.append(self.reg_depth)

    def exit(self, node):
        this_type = self.traverse_node_type.pop()

        if len(self.traverse_node_type) == 0:
            if this_type in ('AbstractComposite', 'AbstractProgram'):
                children_t_depth_list = self.count_stack.pop()
                t_depth = node.merge_t_depth({}, children_t_depth_list)
                self.count_stack.append(t_depth)
                self.reg_depth = self.count_stack[-1]
            else:
                pass
        else:
            parent_node_type = self.traverse_node_type[-1]
            is_abstract = this_type in ('AbstractComposite', 'AbstractProgram')
            parent_is_abstract = parent_node_type in ('AbstractComposite', 'AbstractProgram')

            if is_abstract and parent_is_abstract:
                children_t_depth_list = self.count_stack.pop()
                t_depth = node.merge_t_depth({}, children_t_depth_list)
                self.count_stack[-1].append(t_depth)
                self.reg_depth = None

            elif is_abstract and not parent_is_abstract:
                children_t_depth_list = self.count_stack.pop()
                self.reg_depth = self.count_stack[-1]
                self.reg_depth = node.merge_t_depth(self.reg_depth, children_t_depth_list)

            elif not is_abstract and parent_is_abstract:
                reg_count = self.count_stack.pop()
                self.count_stack[-1].append(reg_count)
                self.reg_depth = None

            else:
                pass

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        if node.program_type() == 'Primitive':
            node.t_depth(self.reg_depth, dagger_ctx, controllers_ctx)

    def get_depth(self):
        return get_depth(self.reg_depth)


# ── Tree Renderers ──

class TreeRenderer:
    """Visitor that renders an Operation tree as an indented tree structure.

    Used by ``Operation.__repr__()`` to generate a hierarchical text
    representation of an operation and its children. Supports folding
    (hiding) of specific module subtrees.

    Example output::

        Toffoli: QRegs(q0[1], q1[1], q2[1])
          CNOT: QRegs(q0[1], q1[1])
          CNOT: QRegs(q1[1], q2[1])
          CNOT: QRegs(q0[1], q1[1])

    Attributes:
        text: Accumulated rendered text.
        indent: Current indentation level (in spaces).
        fold_modules: List of operation names to fold (hide their children).
        folding: Whether currently inside a folded subtree.
        hidden: Whether current node should be hidden.

    Example:
        >>> from pyqres.primitives import Toffoli
        >>> from pyqres.core.metadata import RegisterMetadata
        >>> RegisterMetadata.push_register_metadata()
        >>> RegisterMetadata.get_register_metadata().declare_register('q0', 1)
        >>> RegisterMetadata.get_register_metadata().declare_register('q1', 1)
        >>> RegisterMetadata.get_register_metadata().declare_register('q2', 1)
        >>> t = Toffoli(['q0', 'q1', 'q2'])
        >>> renderer = TreeRenderer()
        >>> t.traverse(renderer)
        >>> print(renderer.text)
    """

    def __init__(self, fold_modules=None):
        """Initialize the renderer.

        Args:
            fold_modules: List of operation names to fold. Children of
                these operations will not be rendered.
        """
        self.text = ""
        self.indent = -2
        self.fold_modules = fold_modules or []
        self.folding = False
        self.hidden = False

    def enter(self, node):
        """Called when entering a node during traversal.

        Increases indent level and manages folding state.

        Args:
            node: The Operation node being entered.
        """
        self.indent += 2
        if self.folding:
            self.hidden = True
        if node.name in self.fold_modules:
            self.folding = True

    def exit(self, node):
        """Called when exiting a node during traversal.

        Decreases indent level and resets folding state when leaving
        a folded module.

        Args:
            node: The Operation node being exited.
        """
        self.indent -= 2
        if node.name in self.fold_modules:
            self.folding = False
            self.hidden = False

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        """Visit a node and render its string representation.

        Calls ``node.render_this()`` to get the formatted string for
        this node, then appends it to the accumulated text.

        Args:
            node: The Operation node to visit.
            dagger_ctx: Whether the node is being traversed in dagger mode.
            controllers_ctx: Current controller context from parent nodes.
        """
        if self.hidden:
            return ""
        self.text += node.render_this(self.indent, dagger_ctx, controllers_ctx)
        self.text += "\n"


class PlainRenderer:
    """Visitor that renders an Operation tree as plain text.

    Similar to TreeRenderer but uses ``plain_render_this()`` which
    provides a simpler output format. Used by ``Operation.__str__()``.

    Example output::

        Toffoli: QRegs(q0[1], q1[1], q2[1])
          CNOT: QRegs(q0[1], q1[1])
          CNOT: QRegs(q1[1], q2[1])
          CNOT: QRegs(q0[1], q1[1])

    Attributes:
        text: Accumulated rendered text.
        indent: Current indentation level (in spaces).
        fold_modules: List of operation names to fold (hide their children).
        folding: Whether currently inside a folded subtree.
        hidden: Whether current node should be hidden.
    """

    def __init__(self, fold_modules=None):
        """Initialize the renderer.

        Args:
            fold_modules: List of operation names to fold. Children of
                these operations will not be rendered.
        """
        self.text = ""
        self.indent = -2
        self.fold_modules = fold_modules or []
        self.folding = False
        self.hidden = False

    def enter(self, node):
        """Called when entering a node during traversal.

        Increases indent level and manages folding state.

        Args:
            node: The Operation node being entered.
        """
        self.indent += 2
        if self.folding:
            self.hidden = True
        if node.name in self.fold_modules:
            self.folding = True

    def exit(self, node):
        """Called when exiting a node during traversal.

        Decreases indent level and resets folding state when leaving
        a folded module.

        Args:
            node: The Operation node being exited.
        """
        self.indent -= 2
        if node.name in self.fold_modules:
            self.folding = False
            self.hidden = False

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        """Visit a node and render its plain string representation.

        Calls ``node.plain_render_this()`` to get the formatted string
        for this node, then appends it to the accumulated text.

        Args:
            node: The Operation node to visit.
            dagger_ctx: Whether the node is being traversed in dagger mode.
            controllers_ctx: Current controller context from parent nodes.
        """
        if self.hidden:
            return ""
        self.text += node.plain_render_this(self.indent, dagger_ctx, controllers_ctx)
        self.text += "\n"


# ── Toffoli-Count Visitor ──

class ToffoliCounter:
    """Visitor that computes total Toffoli gate count via lowering."""

    def __init__(self):
        self.count_stack = [[]]

    def enter(self, node):
        self.count_stack.append([])

    def exit(self, node):
        current = self.count_stack.pop()
        total = node.sum_toffoli_count(current)
        self.count_stack[-1].append(total)

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}
        toffoli_count = node.toffoli_count(dagger_ctx, controllers_ctx)
        if toffoli_count is not None:
            self.count_stack[-1].append(toffoli_count)

    def get_count(self):
        if len(self.count_stack) != 1:
            raise ValueError("Stack is not empty")
        if len(self.count_stack[0]) != 1:
            raise ValueError("Stack top is not a list of length 1")
        return self.count_stack[0][0]


tree_renderer = TreeRenderer()
plain_renderer = PlainRenderer()
