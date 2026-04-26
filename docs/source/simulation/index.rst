PySparQ 模拟
=============

Quantum-Resource-Estimator 通过 :class:`~pyqres.core.simulator.SimulatorVisitor` 对接 PySparQ C++ 量子稀疏态模拟器。

基本用法
--------

.. code-block:: python

   from pyqres import SimulatorVisitor

   # 创建模拟器
   simulator = SimulatorVisitor()

   # 执行操作
   operation.traverse(simulator)

PySparQ 集成
------------

- PySparQ 是 C++ 实现的量子稀疏态模拟器
- 安装方式：``pip install pysparq`` 或通过 ``pip install -e ".[test]"`` 安装完整依赖
- PySparQ 是必需依赖，所有测试都需要安装

Primitive 的模拟
----------------

每个 Primitive 通过 ``pyqsparse_object()`` 方法返回 PySparQ 操作对象：

.. code-block:: python

   class Hadamard(Primitive):
       def pyqsparse_object(self, dagger_ctx=False, controllers_ctx=None):
           from pysparq import Hadamard_Int_Full
           obj = Hadamard_Int_Full(self.reg)
           obj.set_controller(controllers_ctx)
           return obj

Grover 搜索模拟
---------------

使用 :func:`~pyqres.algorithms.grover.grover_search` 执行 Grover 量子搜索：

.. code-block:: python

   from pyqres.algorithms.grover import grover_search

   memory = [5, 12, 3, 8, 21, 34, 7, 15]
   target = 21

   best_addr, prob = grover_search(memory, target)
   print(f"Found at index {best_addr}, probability {prob:.4f}")

Shor 分解模拟
-------------

使用 :func:`~pyqres.algorithms.shor.factor` 执行 Shor 量子分解：

.. code-block:: python

   from pyqres.algorithms.shor import factor

   p, q = factor(15)
   print(f"15 = {p} × {q}")  # 15 = 3 × 5

QRAM 态制备模拟
---------------

使用 :class:`~pyqres.algorithms.state_prep.StatePreparation` 制备任意量子态：

.. code-block:: python

   from pyqres.algorithms.state_prep import StatePreparation

   sp = StatePreparation(qubit_number=3, data_size=8, data_range=4)
   sp.set_distribution([1, 2, 3, 4, 5, 6, 7, 8])
   print(f"归一化振幅: {sp.get_real_dist()}")

块编码模拟
----------

使用 :class:`~pyqres.algorithms.block_encoding.BlockEncodingTridiagonal` 对三对角矩阵进行块编码：

.. code-block:: python

   from pyqres.algorithms.block_encoding import get_tridiagonal_matrix

   alpha = [1.0, 2.0, 3.0]
   beta  = [0.5, 0.5]
   gamma = [0.5, 0.5]

   mat = get_tridiagonal_matrix(alpha, beta, gamma)
   print(f"矩阵元素: {mat}")
