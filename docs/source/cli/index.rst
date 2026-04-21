命令行工具
==========

Quantum-Resource-Estimator 提供 ``pyqres`` 命令行工具。

compile
-------

编译 YAML schema 生成 Python 代码：

.. code-block:: bash

   # 编译默认 schemas
   pyqres compile

   # 指定源和输出路径
   pyqres compile --source pyqres/dsl/schemas/primitives/ --output pyqres/generated/

check
-----

检查操作定义的完整性：

.. code-block:: bash

   pyqres check

检查内容：

- 依赖图构建与缺失检测
- 循环依赖检测
- 覆盖率报告

show
----

显示操作的依赖树：

.. code-block:: bash

   # 显示操作树
   pyqres show Swap

   # 限制深度
   pyqres show Swap --depth 3

estimate
--------

估计操作的资源消耗：

.. code-block:: bash

   # 估计 T-count（默认）
   pyqres estimate Toffoli

   # 指定寄存器大小
   pyqres estimate Add_UInt_UInt -r a:4,b:4,c:4

   # 估计 T-depth
   pyqres estimate Toffoli -m t_depth

   # 估计 Toffoli-count
   pyqres estimate Mult_UInt_ConstUInt -r a:4,b:4 -p const:5 -m toffoli_count

参数说明：

- ``operation`` — 操作名称（必须存在于 OperationRegistry）
- ``-r, --registers`` — 寄存器定义，格式为 ``name:size,name:size,...``
- ``-p, --params`` — 参数定义，格式为 ``name:value,name:value,...``
- ``-m, --metric`` — 资源指标：``t_count``（默认）、``t_depth``、``toffoli_count``