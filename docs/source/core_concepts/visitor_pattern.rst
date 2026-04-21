访问者模式
==========

Quantum-Resource-Estimator 使用访问者模式遍历操作树进行资源估计和模拟。

遍历机制
--------

调用 ``operation.traverse(visitor)`` 时，对每个节点：

1. ``enter(node)`` - 进入节点（压栈）
2. ``visit(node, dagger_ctx, controllers_ctx)`` - 访问节点
3. 遍历子节点（递归）
4. ``exit(node)`` - 退出节点（弹栈）

遍历示例
--------

以树结构 ``A → [X, Y, Z]`` 为例：

::

   1. visitor.enter(A), visitor.visit(A)
   2. visitor.enter(X), visitor.visit(X), visitor.exit(X)
   3. visitor.enter(Y), visitor.visit(Y), visitor.exit(Y)
   4. visitor.enter(Z), visitor.visit(Z), visitor.exit(Z)
   5. visitor.exit(A)

内置访问者
----------

TCounter
~~~~~~~~

计算 T 门总数：

.. code-block:: python

   from pyqres import TCounter

   counter = TCounter()
   operation.traverse(counter)
   t_count = counter.get_result()

TDepthCounter
~~~~~~~~~~~~~

计算 T 门深度：

.. code-block:: python

   from pyqres import TDepthCounter

   counter = TDepthCounter()
   operation.traverse(counter)
   t_depth = counter.get_result()

SimulatorVisitor
~~~~~~~~~~~~~~~~

在 PySparQ 模拟器上执行操作：

.. code-block:: python

   from pyqres import SimulatorVisitor

   simulator = SimulatorVisitor()
   operation.traverse(simulator)

自定义访问者
------------

实现自定义 Visitor 需定义 ``enter``、``visit``、``exit`` 方法：

.. code-block:: python

   class MyVisitor:
       def enter(self, node):
           print(f"Entering {node.__class__.__name__}")

       def visit(self, node, dagger_ctx=False, controllers_ctx=None):
           print(f"Visiting {node.__class__.__name__}")

       def exit(self, node):
           print(f"Exiting {node.__class__.__name__}")