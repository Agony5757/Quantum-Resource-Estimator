from ..core.metadata import RegisterMetadata
from ..core.utils import merge_controllers
from .generator import QuantumCircuit, OpCode, Controller, LatexGenerator


class QuantikzVisitor:
    """Visitor that converts an Operation tree into a LaTeX quantum circuit diagram."""

    def __init__(self):
        registers = RegisterMetadata.get_registers()
        self.circuit = QuantumCircuit(registers)
        self._skip = None

    def enter(self, node):
        if self._skip:
            return

    def exit(self, node):
        if id(node) == self._skip:
            self._skip = None

    def visit(self, node, dagger_ctx=False, controllers_ctx=None):
        controllers_ctx = controllers_ctx or {}

        if hasattr(node, 'pyqsparse_object'):
            op_code = self._primitive_to_opcode(node, dagger_ctx, controllers_ctx)
            if op_code is not None:
                self.circuit.add_op(op_code)
            self._skip = id(node)
        elif hasattr(node, 'program_list'):
            # Register ops like SplitRegister/CombineRegister
            self._handle_register_op(node, dagger_ctx, controllers_ctx)
            self._skip = id(node)

    def _primitive_to_opcode(self, node, dagger_ctx=False, controllers_ctx=None):
        merged = merge_controllers(node.controllers, controllers_ctx or {})
        dagger = dagger_ctx ^ node.dagger_flag

        name = node.name
        targets = list(node.reg_list)
        params = list(node.param_list)

        controls = self._build_controls(merged)

        return OpCode(
            name=name,
            targets=targets,
            params=params,
            controls=controls,
            dagger=dagger,
        )

    def _build_controls(self, controllers_ctx):
        controls = []
        for ctype in ('conditioned_by_all_ones', 'conditioned_by_nonzero',
                       'conditioned_by_bit', 'conditioned_by_value'):
            if ctype in controllers_ctx:
                for entry in controllers_ctx[ctype]:
                    if isinstance(entry, tuple):
                        reg, info = entry[0], entry[1]
                        controls.append(Controller(qreg=reg, control_type=ctype, control_info=info))
                    else:
                        controls.append(Controller(qreg=entry, control_type=ctype))
        return controls

    def _handle_register_op(self, node, dagger_ctx, controllers_ctx):
        name = node.name
        if name == 'SplitRegister':
            self.circuit.split_registers(node.reg_list, node.param_list)
        elif name == 'CombineRegister':
            self.circuit.merge_registers(node.reg_list, node.param_list)

    def to_latex(self):
        return LatexGenerator.generate(self.circuit)

    def to_latex_figure(self, caption=""):
        return LatexGenerator.generate_as_figure(self.circuit, caption)
