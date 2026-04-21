组合操作
========

组合操作 (Composite) 由多个子操作构成，形成操作树的内部节点。

StandardComposite
-----------------

默认行为：子操作 T-count 简单求和。

.. code-block:: python

   from pyqres.core.operation import StandardComposite

   class MyComposite(StandardComposite):
       def __init__(self, reg_list, param_list=None):
           super().__init__(reg_list=reg_list, param_list=param_list)
           self.program_list = [
               Hadamard([self.reg_list[0]]),
               CNOT([self.reg_list[0], self.reg_list[1]]),
           ]
           self.declare_program_list()

AbstractComposite
-----------------

自定义 T-count 聚合逻辑，重写 ``sum_t_count()`` 方法。

.. code-block:: python

   from pyqres.core.operation import AbstractComposite

   class AmplitudeAmplification(AbstractComposite):
       def __init__(self, reg_list, param_list=None):
           super().__init__(reg_list=reg_list, param_list=param_list)
           # ... 构建 program_list

       def sum_t_count(self, t_count_list):
           # 自定义聚合公式
           t_oracle = t_count_list[0]
           t_diffusion = t_count_list[1]
           iterations = ...  # 迭代次数
           return (t_oracle + t_diffusion) * iterations

YAML 生成
---------

组合操作通常通过 YAML DSL 定义，由 ``pyqres compile`` 自动生成 Python 代码。
详见 :doc:`yaml_dsl`。