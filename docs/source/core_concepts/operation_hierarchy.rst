操作类层次结构
==============

Quantum-Resource-Estimator 的核心是 :class:`~pyqres.core.operation.Operation` 类层次。

类层次关系
----------

- :class:`~pyqres.core.operation.Operation` - 基类，所有操作的祖先
- :class:`~pyqres.core.operation.Primitive` - 原语操作，叶节点，直接映射 PySparQ 操作
- :class:`~pyqres.core.operation.Composite` - 组合操作，由子操作构成
- :class:`~pyqres.core.operation.StandardComposite` - 默认 T-count 求和的组合操作
- :class:`~pyqres.core.operation.AbstractComposite` - 自定义 T-count 聚合的组合操作

Primitive vs Composite
----------------------

**Primitive (原语)**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - 特征
     - 说明
   * - 继承
     - :class:`~pyqres.core.operation.Primitive`
   * - 节点类型
     - 叶节点
   * - 必须实现
     - ``t_count()``, ``pyqsparse_object()``
   * - 子操作
     - 无

**Composite (组合)**

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - 特征
     - 说明
   * - 继承
     - :class:`~pyqres.core.operation.Composite`
   * - 节点类型
     - 内部节点
   * - 必须实现
     - ``__init__()`` 中构建 ``program_list``
   * - 子操作
     - 有，存储在 ``program_list``

使用方式
--------

.. code-block:: python

   from pyqres import Hadamard, CNOT, TCounter

   # Primitive：直接计算 T-count
   h = Hadamard(['q'])
   print(h.t_count())  # 0

   # Composite：遍历子操作求和
   swap = Swap_General_General(['q1', 'q2'])
   counter = TCounter()
   swap.traverse(counter)
   print(counter.get_result())