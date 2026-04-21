Quantikz 线路图
===============

Quantum-Resource-Estimator 支持使用 Quantikz LaTeX 包生成量子线路图。

生成线路图
----------

.. code-block:: python

   from pyqres.quantikz import QuantumCircuit

   # 创建线路图
   circuit = QuantumCircuit()
   # ... 添加操作

   # 生成 LaTeX
   latex = circuit.to_latex()

依赖
----

- LaTeX 系统（需安装 ``pdflatex``）
- ``quantikz2`` LaTeX 包