YAML Schema 结构
================

本页详细说明 YAML schema 的结构和字段。

完整字段参考
------------

.. list-table::
   :widths: 20 15 65
   :header-rows: 1

   * - 字段
     - 必选
     - 说明
   * - ``name``
     - 是
     - 类名（PascalCase），如 ``Hadamard``、``Swap``
   * - ``description``
     - 否
     - 操作描述，用于文档生成
   * - ``qregs``
     - 是
     - 量子寄存器列表
   * - ``params``
     - 否
     - 经典参数列表
   * - ``temp_regs``
     - 否
     - 临时寄存器（自动生命周期管理）
   * - ``is_primitive``
     - 否
     - ``true`` = primitive，省略 = composed
   * - ``pysparq_op``
     - 原语必选
     - PySparQ 操作类名，或 ``conditional``
   * - ``pysparq_args``
     - 原语必选
     - 构造参数列表，使用 ``$name`` 引用
   * - ``t_count``
     - 原语必选
     - T-count 公式（Python 代码片段）
   * - ``impl``
     - 组合必选
     - 子操作列表
   * - ``computed_params``
     - 否
     - 派生参数，从 params 计算得到
   * - ``traverse_override``
     - 否
     - 特殊遍历逻辑标记，如 ``cnot_swap``
   * - ``custom_pyqsparse``
     - 否
     - 手写 pyqsparse_object 代码

寄存器声明
----------

``qregs`` 和 ``temp_regs`` 的格式：

.. code-block:: yaml

   qregs:
     - {name: reg1, type: General}
     - {name: reg2, type: UnsignedInteger}
     - {name: flag, type: Boolean}

   temp_regs:
     - {name: overflow, size: 1}
     - {name: ancilla, size: 4}

寄存器类型：

- ``General`` - 广义量子态
- ``UnsignedInteger`` - 无符号整数
- ``SignedInteger`` - 有符号整数
- ``Boolean`` - 单比特布尔
- ``Rational`` - 定点有理数

参数声明
--------

``params`` 的格式：

.. code-block:: yaml

   params:
     - {name: epsilon, type: float}
     - {name: kappa, type: symbol}
     - {name: data, type: array}

参数类型：

- ``int`` - 整数
- ``float`` - 浮点数
- ``symbol`` - SymPy 符号
- ``array`` - 数组
- ``object`` - 任意对象
- ``str`` - 字符串
- ``bool`` - 布尔值

子操作列表
----------

``impl`` 的格式：

.. code-block:: yaml

   impl:
     - op: CNOT
       qregs: [reg1, reg2]
     - op: Hadamard
       qregs: [reg1]
       dagger: true
     - op: Add_UInt_UInt
       qregs: [a, b]
       params: [epsilon]
       controllers:
         all_ones: [ctrl_reg]

控制类型
--------

在 ``controllers`` 中指定：

.. code-block:: yaml

   controllers:
     nonzero: [reg]           # reg 非零时触发
     all_ones: [reg]          # reg 全 1 时触发
     bit: [[reg, index]]      # reg 的第 index 位为 1 时触发
     value: [[reg, val]]      # reg == val 时触发

示例
----

完整的 Swap 操作定义：

.. code-block:: yaml

   - name: Swap
     description: "通过 3 个 CNOT 交换两个寄存器"
     qregs:
       - {name: reg1, type: General}
       - {name: reg2, type: General}
     impl:
       - op: CNOT
         qregs: [reg1, reg2]
       - op: CNOT
         qregs: [reg2, reg1]
       - op: CNOT
         qregs: [reg1, reg2]
     traverse_override: cnot_swap