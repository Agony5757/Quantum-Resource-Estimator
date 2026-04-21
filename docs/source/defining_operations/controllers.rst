控制器链
========

Quantum-Resource-Estimator 支持通过 ``control()`` 方法为操作添加控制条件，形成控制器链。

控制类型
--------

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - 类型
     - 说明
   * - ``nonzero``
     - 寄存器非零时触发
   * - ``all_ones``
     - 寄存器所有位为 1 时触发
   * - ``bit``
     - 指定位为 1 时触发
   * - ``value``
     - 寄存器等于指定值时触发

流式 API
--------

使用 ``control()`` 方法叠加控制条件：

.. code-block:: python

   from pyqres import CNOT

   # 单一控制
   cnot = CNOT(['q1', 'q2']).control('ctrl')

   # 多重控制（链式调用）
   cnot = CNOT(['q1', 'q2']).control('ctrl1').control('ctrl2')

转置操作
--------

使用 ``dagger()`` 方法获取操作的逆：

.. code-block:: python

   from pyqres import QFT

   # 正向 QFT
   qft = QFT(['data'])

   # 逆向 QFT（等价于 InverseQFT）
   qft_inv = qft.dagger()

   # 组合使用
   from pyqres import Add_UInt_UInt
   add = Add_UInt_UInt(['a', 'b']).dagger().control('ctrl')

YAML 中的控制
-------------

在 YAML 的 ``impl`` 中指定控制条件：

.. code-block:: yaml

   impl:
     - op: PlusOneAndOverflow
       qregs: [main_reg, overflow]
       controllers:
         value: [[anc_UA, 1]]
     - op: X
       qregs: [other]
       params: [0]
       controllers:
         all_ones: [anc_UA]