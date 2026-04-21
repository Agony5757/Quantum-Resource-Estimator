YAML DSL
========

Quantum-Resource-Estimator 使用 YAML 作为操作定义的 schema 格式，支持静态生成 Python 类。

基本流程
--------

::

   YAML Schema → SchemaValidator → CodeGenerator → generated/*.py

1. 在 ``pyqres/dsl/schemas/`` 下编写 YAML 文件
2. 运行 ``pyqres compile`` 编译
3. 生成的 Python 类自动注册到 OperationRegistry

Primitive 定义
--------------

.. code-block:: yaml

   - name: Hadamard
     description: "Hadamard on full register"
     qregs:
       - {name: reg, type: General}
     is_primitive: true
     pysparq_op: Hadamard_Int_Full
     pysparq_args: ["$reg"]
     t_count: |
       if ncontrols == 0:
           return 0
       else:
           raise NotImplementedError

Composed 定义
-------------

.. code-block:: yaml

   - name: Swap
     description: "Swap two registers via 3 CNOTs"
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

Schema 字段
-----------

.. list-table::
   :widths: 20 15 65
   :header-rows: 1

   * - 字段
     - 必选
     - 说明
   * - ``name``
     - 是
     - 类名（PascalCase）
   * - ``qregs``
     - 是
     - 量子寄存器列表，每项含 name/type
   * - ``params``
     - 否
     - 经典参数列表
   * - ``temp_regs``
     - 否
     - 临时寄存器（enter 声明、exit 移除）
   * - ``is_primitive``
     - 否
     - true = primitive，省略 = composed
   * - ``pysparq_op``
     - 原语必选
     - PySparQ 操作类名，或 ``conditional``
   * - ``pysparq_args``
     - 原语必选
     - 构造参数，``$name`` 引用 qreg/param
   * - ``t_count``
     - 原语必选
     - T-count 公式（Python 代码片段）
   * - ``impl``
     - 组合必选
     - 子操作列表
   * - ``computed_params``
     - 否
     - 从 params 计算的派生属性
   * - ``traverse_override``
     - 否
     - 特殊遍历逻辑标记

``$name`` 语法：引用当前操作的 qreg 或 param，生成代码时替换为 ``self.name``。