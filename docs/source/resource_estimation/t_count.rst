T-count 估计
============

T-count 是容错量子计算的关键资源指标，表示 T 门的数量。

计算方法
--------

使用 :class:`~pyqres.core.visitor.TCounter` 遍历操作树：

.. code-block:: python

   from pyqres import TCounter

   counter = TCounter()
   operation.traverse(counter)
   t_count = counter.get_result()

T-count 规则
------------

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - 节点类型
     - T-count 行为
   * - Primitive
     - 必须定义 ``t_count()`` 方法
   * - StandardComposite
     - 子节点 T-count 简单求和
   * - AbstractComposite
     - 重写 ``sum_t_count()`` 自定义聚合

Primitive 的 T-count
~~~~~~~~~~~~~~~~~~~~

直接通过寄存器大小和参数计算：

.. code-block:: python

   class CNOT(Primitive):
       def t_count(self, dagger_ctx=False, controllers_ctx=None):
           ncontrols = get_control_qubit_count(controllers_ctx)
           if ncontrols == 0:
               return 0
           else:
               return mcx_t_count(ncontrols)

AbstractComposite 的 T-count
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

使用自定义公式聚合子操作的 T-count：

.. code-block:: python

   class LinearSolver(AbstractComposite):
       def sum_t_count(self, t_count_list):
           t_A = t_count_list[0]
           t_b = t_count_list[1]
           kappa, epsilon = self.kappa, self.epsilon
           Q = 56*kappa + 1.05*kappa * log(sqrt(1-epsilon**2)/epsilon) + ...
           return (t_A + 2*t_b) * Q

使用 LoweringEngine
-------------------

:class:`~pyqres.core.lowering.LoweringEngine` 提供更高级的资源估计接口：

.. code-block:: python

   from pyqres.core.lowering import TCountEstimator

   estimator = TCountEstimator()
   t_count = estimator.estimate(operation)