Toffoli-count 估计
==================

Toffoli-count 是量子算法复杂度的常用近似指标。由于 Toffoli 门消耗 7 个 T 门，Toffoli-count 可由 T-count 除以 7 得到。

计算方法
--------

使用 :class:`~pyqres.core.visitor.ToffoliCounter` 遍历操作树：

.. code-block:: python

   from pyqres.core.visitor import ToffoliCounter

   counter = ToffoliCounter()
   operation.traverse(counter)
   toffoli_count = counter.get_result()

使用 LoweringEngine
-------------------

:class:`~pyqres.core.lowering.LoweringEngine` 提供更高级的接口：

.. code-block:: python

   from pyqres.core.lowering import ToffoliCountEstimator

   estimator = ToffoliCountEstimator()
   toffoli_count = engine.estimate(operation, estimator)

CLI 命令
--------

.. code-block:: bash

   pyqres estimate Toffoli -m toffoli_count
   # Output: toffoli_count: 1

计算公式
--------

每个 Primitive 的 Toffoli-count 由其 ``toffoli_count()`` 方法计算：

.. code-block:: python

   class Primitive:
       def toffoli_count(self, dagger_ctx=False, controllers_ctx=None):
           t = self.t_count(dagger_ctx, controllers_ctx)
           if t is None:
               return None
           return t // 7

对于组合操作，Toffoli-count 为子操作求和。
