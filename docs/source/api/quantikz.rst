pyqres.quantikz
===============

.. warning::

   ``pyqres.quantikz`` 模块当前正在重构中，暂时不可用。

   该模块将适配新的 Operation 类层次结构后重新启用。

模块概述
--------

quantikz 模块提供 Quantikz LaTeX 量子线路图生成功能，包含以下核心类：

- :class:`~pyqres.quantikz.generator.QuantumCircuit` - 量子电路表示
- :class:`~pyqres.quantikz.generator.QReg` - 量子寄存器
- :class:`~pyqres.quantikz.generator.OpCode` - 操作码数据类
- :class:`~pyqres.quantikz.generator.Controller` - 控制器数据类
- :class:`~pyqres.quantikz.generator.LatexGenerator` - LaTeX 代码生成器
- :class:`~pyqres.quantikz.generator.Compiler` - LaTeX 编译器

使用示例（重构完成后）
----------------------

从操作树生成 LaTeX 线路图：

.. code-block:: python

   from pyqres.quantikz.generator import (
       QuantumCircuit, OpCode, Controller, LatexGenerator, Compiler
   )

   # 创建电路
   circuit = QuantumCircuit({'q1': 1, 'q2': 1, 'ctrl': 1})

   # 添加操作
   circuit.add_op(OpCode(
       name='CNOT',
       targets=['q1'],
       controls=[Controller('ctrl', 'conditioned_by_all_ones')]
   ))
   circuit.add_op(OpCode(name='H', targets=['q2']))

   # 生成 LaTeX
   latex_code = LatexGenerator.generate(circuit)

   # 编译为 PDF
   Compiler.compile(latex_code, 'my_circuit.tex')

依赖要求
--------

- quantikz2 TikZ 库
- pdflatex（用于编译 PDF）
