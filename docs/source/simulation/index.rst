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