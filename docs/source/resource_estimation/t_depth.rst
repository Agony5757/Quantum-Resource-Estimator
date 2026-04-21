T-depth 估计
============

T-depth 表示 T 门电路的关键路径深度，是并行化能力的重要指标。

计算方法
--------

使用 :class:`~pyqres.core.visitor.TDepthCounter` 遍历操作树：

.. code-block:: python

   from pyqres import TDepthCounter

   counter = TDepthCounter()
   operation.traverse(counter)
   t_depth = counter.get_result()

T-count vs T-depth
------------------

- **T-count**：T 门总数，反映总体资源消耗
- **T-depth**：T 门关键路径深度，反映时间复杂度

两者均通过 Visitor 模式计算，使用相同的 ``traverse()`` 接口。