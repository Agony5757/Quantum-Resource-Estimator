快速入门
========

基本概念
--------

Quantum-Resource-Estimator 采用 **寄存器级编程范式**，将量子程序表示为操作树。

- **寄存器 (Register)**：量子比特的集合，可编码整数、布尔值等
- **操作 (Operation)**：对寄存器执行的量子门或复合子程序
- **遍历 (Traverse)**：通过 Visitor 模式遍历操作树进行资源估计

第一个例子
----------

计算 Hadamard 门的 T-count：

.. code-block:: python

   from pyqres import Hadamard, TCounter
   from pyqres.core.metadata import RegisterMetadata

   # 声明寄存器
   RegisterMetadata.declare_register('q', 1)

   # 创建操作
   h = Hadamard(['q'])

   # 计算 T-count
   counter = TCounter()
   h.traverse(counter)
   print(f"T-count: {counter.get_result()}")  # T-count: 0

创建组合操作
------------

组合多个基本门形成复杂操作：

.. code-block:: python

   from pyqres import CNOT, Swap_General_General

   # 声明寄存器
   RegisterMetadata.declare_register('q1', 1)
   RegisterMetadata.declare_register('q2', 1)

   # Swap 操作（由 3 个 CNOT 组成）
   swap = Swap_General_General(['q1', 'q2'])

   # 计算 T-count
   counter = TCounter()
   swap.traverse(counter)
   print(f"T-count: {counter.get_result()}")

使用控制操作
------------

为操作添加控制条件：

.. code-block:: python

   # 受控 CNOT
   cnot_controlled = CNOT(['q1', 'q2']).control('q3')

   # 计算 T-count（受控 CNOT 有 T 门开销）
   counter = TCounter()
   cnot_controlled.traverse(counter)
   print(f"T-count: {counter.get_result()}")