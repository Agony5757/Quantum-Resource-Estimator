# Generated from YAML definition

from ..core.operation import StandardComposite
from ..core.registry import OperationRegistry
from ..core.utils import merge_controllers
import math

class BlockEncodingViaQRAM(StandardComposite):
    """Block encoding via QRAM: U_A = SWAP · UR† · UL (interface definition)"""
    def __init__(self, reg_list, param_list=None):
        if param_list is None:
            param_list = []
        StandardComposite.__init__(self, reg_list=reg_list, param_list=param_list)
        self.row_index = reg_list[0]
        self.column_index = reg_list[1]
        self.data_size = param_list[0]
        self.rational_size = param_list[1]
        self.qram = param_list[2]
        # Complex implementation with loops/conditionals
        self._impl_structure = [{"_type": "comment", "text": "UL(row, col) \u2014 left-multiplication operator (Python class, needs qram runtime)"}, {"_type": "comment", "text": "UR(col) dagger \u2014 right-multiplication operator (Python class, needs qram runtime)"}, {"_type": "comment", "text": "Swap(row, col) \u2014 swap row and column index registers"}]
        self._build_execute_method()

    def _build_execute_method(self):
        # Build program_list by expanding loops and conditionals
        self.program_list = []
        # UL(row, col) — left-multiplication operator (Python class, needs qram runtime)
        # UR(col) dagger — right-multiplication operator (Python class, needs qram runtime)
        # Swap(row, col) — swap row and column index registers
        self.declare_program_list()