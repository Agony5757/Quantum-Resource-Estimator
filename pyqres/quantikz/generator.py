from dataclasses import dataclass, field
import os
from pathlib import Path
import subprocess
from typing import List, Dict, Union
from sympy import Symbol, latex

class QReg:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
    
    def __hash__(self):
        return hash(self.name + str(self.size))
    
    def __eq__(self, value):
        return self.name == value.name and self.size == value.size
    
    def __str__(self):
        return f"{self.name}[{self.size}]"
    
    def __repr__(self):
        return f"{self.name}[{self.size}]"

@dataclass
class Controller:
    qreg: str
    control_type: str
    control_info: any = None

@dataclass
class OpCode:
    name: str
    targets: List[str]
    params: List[Union[float, Symbol]] = field(default_factory=list)
    controls: List[Controller] = field(default_factory=list)
    dagger : bool = False

class QuantumCircuit:
    def __init__(self, registers: Dict[str, int]):
        self.registers = {name: QReg(name, size) for name, size in registers.items()}
        self.timeline = []
    
    def add_op(self, op: OpCode):
        self.timeline.append(op)

    def split_registers(self, reg_list, param_list):
        reg0 = self.registers[reg_list[0]]

        for reg_name, new_size in zip(reg_list[1:], param_list):
            reg = self.registers[reg_name]
            reg0.size -= new_size
            reg.size += new_size
        

    def merge_registers(self, reg_list, param_list):
        reg0 = self.registers[reg_list[0]]

        for reg_name, new_size in zip(reg_list[1:], param_list):
            reg = self.registers[reg_name]
            reg0.size += reg.size
            reg.size -= new_size
            
        
class LatexGenerator:
    @staticmethod
    def generate(circuit: QuantumCircuit) -> str:
        gen = LatexGenerator(circuit)
        return gen._build_full_document()
    
    @staticmethod
    def generate_as_figure(circuit: QuantumCircuit, figure_caption: str) -> str:
        gen = LatexGenerator(circuit)
        return gen._build_as_figure(figure_caption)

    def __init__(self, circuit: QuantumCircuit):
        self.circuit = circuit
        self.lines = []
        self.current_order = []
        self._init_lines()

    def _init_lines(self):
        """初始化每行的起始部分"""
        self.lines = [
            [f"\\lstick{{${reg.name}$}} & \\qwbundle{{{reg.size}}}"] 
            for reg in self.circuit.registers.values()
        ]
        self.current_order = list(self.circuit.registers.keys())

    def _build_full_document(self) -> str:
        """构建完整LaTeX文档"""
        layers = self._process_into_layers(self.circuit.timeline)

        for ops, qubits in layers:
            self._process_operation_layer(ops)
        
        self._finalize_lines()
        return self._assemble_document()
    
    def _build_as_figure(self, figure_caption) -> str:
        """构建完整LaTeX文档"""
        layers = self._process_into_layers(self.circuit.timeline)

        for ops, qubits in layers:
            self._process_operation_layer(ops)
        
        self._finalize_lines()
        return self._assemble_as_figure(figure_caption)

    def _process_into_layers(self, ops: List[OpCode]) -> List[List[OpCode]]:
        """将操作分层"""

        # 每一层由操作+已经含有的量子比特构成
        layers = [(list(),set())]
        for op in ops:
            # 找到layers中第一个可以包含op的层
            for i, (layer, qubits) in enumerate(layers):
                op_qubits = set(op.targets + LatexGenerator._get_control_regs(op.controls))

                #查看是否有交集，如果没有交集，则可以放入该层
                if not any(q in qubits for q in op_qubits):
                    layers[i] = (layer + [op], qubits.union(set(op.targets + LatexGenerator._get_control_regs(op.controls))))
                    break
            else:
                # 找不到合适的层，新建层
                layers.append(([op], set(op.targets + LatexGenerator._get_control_regs(op.controls))))

        return layers

    def _process_operation(self, op: OpCode):
        """处理单个量子操作"""
        new_order = self._calculate_new_order(op)
        self._handle_permutation(new_order)        
        self._sync_targets(op.targets + LatexGenerator._get_control_regs(op.controls))
        self._add_gate_operation(op)
        self._add_control_lines(op)
    
    @staticmethod
    def _get_control_regs(controls: List[Controller]) -> List[str]:
        """获取控制比特"""
        return [c.qreg for c in controls]

    @staticmethod
    def extract_layer_involved_qregs(ops: List[OpCode]) -> List[str]:
        """提取所有操作的量子比特"""
        qubits = []
        for op in ops:
            qubits += op.targets + LatexGenerator._get_control_regs(op.controls)

        return qubits

    def _process_operation_layer(self, ops: List[OpCode]):
        """处理一层量子操作"""
        new_order = self._calculate_new_order(LatexGenerator.extract_layer_involved_qregs(ops))
        self._handle_permutation(new_order)
        self._sync_targets(LatexGenerator.extract_layer_involved_qregs(ops))
        for op in ops:
            self._add_gate_operation(op)
            self._add_control_lines(op)

    def _calculate_new_order(self, involved: List[str]) -> List[str]:
        """计算需要的新寄存器顺序"""
        # involved = op.targets + LatexGenerator._get_control_regs(op.controls)
        return [r for r in involved if r in self.current_order] + \
               [r for r in self.current_order if r not in involved]

    def _handle_permutation(self, new_order: List[str]):
        """处理寄存器置换逻辑"""
        if new_order == self.current_order:
            return

        perm_indices = [str(self.current_order.index(r)+1) for r in new_order]        
        self._add_permute_command(perm_indices)
        self.current_order = new_order
        self._update_labels_after_permutation()

    def _add_permute_command(self, perm_indices: List[str]):
        """添加permute命令到第一行"""

        self._sync_all()
        cmd = f"\\permute{{{','.join(perm_indices)}}}"
        self._add_to_line(0, cmd)
        for i in range(1, len(self.lines)):
            self._add_to_line(i, " ")

    def _update_labels_after_permutation(self):
        """置换后更新所有寄存器标签"""
        for i, reg_name in enumerate(self.current_order):
            reg_size = self.circuit.registers[reg_name].size
            self._add_to_line(i, f"\\push{{{reg_name}}} \\qwbundle{{{reg_size}}}")

    def _sync_targets(self, targets : List[str]):
        """同步目标线路的列数"""
        max_len = max(len(self.lines[self.current_order.index(target)]) for target in targets)
        for target in set(targets):
            line_idx = self.current_order.index(target)
            line = self.lines[line_idx]
            while len(line) < max_len:
                line.append("& \\qw")

    def _sync_all(self):
        """同步所有线路的列数"""
        max_len = max(len(line) for line in self.lines)
        for line in self.lines:
            while len(line) < max_len:
                line.append("& \\qw")

    def _add_gate_operation(self, op: OpCode):
        """添加门操作到线路"""
        gate_str = self._format_gate(op)
        target_count = len(op.targets)
        
        for i, target in enumerate(op.targets):
            line_idx = self.current_order.index(target)
            cmd = f"\\gate[{target_count}]{{{gate_str}}}" if i == 0 else "\\ghost{}"
            self._add_to_line(line_idx, cmd)
        

    def _add_control_lines(self, op: OpCode):
        """添加控制线"""
        if not op.controls:
            return

        main_target_idx = self.current_order.index(op.targets[0])
        existed_controls = set()
        for control in op.controls:
            control_idx = self.current_order.index(control.qreg)
            
            if control_idx in existed_controls:
                raise NotImplementedError("Multiple controls on the same qubit are not supported yet.")
            existed_controls.add(control_idx)

            delta = main_target_idx - control_idx

            control_type = control.control_type
            if control_type == 'conditioned_by_all_ones':
                self._add_to_line(control_idx, f"\\ctrl{{{delta}}}")
            elif control_type == 'conditioned_by_nonzero':
                self._add_to_line(control_idx, f"\\ctrl[open]{{{delta}}}\\midstick[1,brackets=none]{{$\\neq 0$}}")
            elif control_type == 'conditioned_by_value':
                value = control.control_info
                self._add_to_line(control_idx, f"\\ctrl[open]{{{delta}}}\\midstick[1,brackets=none]{{={value}}}")
            elif control_type == 'conditioned_by_bit':
                bit = control.control_info
                self._add_to_line(control_idx, f"\\ctrl[open]{{{delta}}}\\midstick[1,brackets=none]{{[{bit}]}}")
            else:
                raise ValueError(f"Unknown control type: {control_type}")
            
    def _restore_original_order(self):
        """恢复原始寄存器顺序"""
        if self.current_order == self.circuit.registers:
            return

        rev_perm = [str(self.current_order.index(r)+1) for r in self.circuit.registers.keys()]
        self._add_permute_command(rev_perm)
        self.current_order = list(self.circuit.registers.keys())
        self._update_labels_after_permutation()

    def _add_to_line(self, line_idx: int, command: str):
        """向指定行添加命令"""
        self.lines[line_idx].append(f"& {command}")

    def _finalize_lines(self):
        """为每行添加结束标记"""
        self._restore_original_order()
        for i in range(len(self.lines)):
            self._add_to_line(i, "\\qw")
            self.lines[i].append("\\\\")

    def _assemble_document(self) -> str:
        """组合所有部分生成最终文档"""
        body = ["\n".join(line) for line in self.lines]
        return "\n".join([
            r"\documentclass{standalone}",
            r"\usepackage{tikz}",
            r"\usetikzlibrary{quantikz2}",
            r"\begin{document}",
            r"\begin{quantikz}",
            *body,
            r"\end{quantikz}",
            r"\end{document}"
        ])

    def _assemble_as_figure(self, figure_caption) -> str:
        """组合所有部分生成最终文档"""
        body = ["\n".join(line) for line in self.lines]
        return "\n".join([
            r"\begin{figure}",
            r"\begin{quantikz}",
            *body,
            r"\end{quantikz}",
            r"\caption{" + figure_caption + r"}",
            r"\end{figure}"
        ])

    @staticmethod
    def _format_gate(op: OpCode) -> str:
        """格式化门参数"""
        params = LatexGenerator._format_params(op.params)
        dagger = "^\\dagger" if op.dagger else ""
        return f"\\mathrm{{{op.name}}}{dagger}{params}"

    @staticmethod
    def _format_params(params) -> str:
        """格式化参数列表"""
        if not params:
            return ""
        param_strs = []
        for p in params:
            if isinstance(p, Symbol):
                param_strs.append(latex(p))
            elif isinstance(p, float):
                param_strs.append(f"{p:.2f}".rstrip('0').rstrip('.'))
            else:
                param_strs.append(str(p))
        return f"({', '.join(param_strs)})"
    

class Compiler:
    @staticmethod
    def compile(latex_code: str, filename, tex_path = 'tex_outputs', pdf_path = 'pdf_outputs'):
        """编译LaTeX代码"""

        os.makedirs(tex_path, exist_ok=True)
        os.makedirs(pdf_path, exist_ok=True)

        tex_path = Path(tex_path)
        pdf_path = Path(pdf_path)
        pdf_path_ = str(pdf_path).replace("\\", "/")
        with open(tex_path / filename, "w") as f:
            f.write(latex_code)
        
        texfile = str(tex_path / f"{filename}")
        texfile = texfile.replace("\\", "/")
        # print(f"Compiling {texfile}...")
        # print("Output directory:", pdf_path_)

        ret = subprocess.run([
            "pdflatex",
            f"-output-directory={pdf_path_}",
            texfile,     
        ], capture_output=True)
        if ret.returncode != 0:
            print(ret.stdout.decode())
            print(ret.stderr.decode())
            raise RuntimeError("LaTeX compilation failed!")
        
        os.remove(pdf_path / filename.replace(".tex", ".aux"))
        os.remove(pdf_path / filename.replace(".tex", ".log"))

