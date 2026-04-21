原语操作
========

原语操作 (Primitive) 是操作树的叶节点，直接映射到 PySparQ 模拟器操作。

基本特征
--------

- 继承 :class:`~pyqres.core.operation.Primitive`
- 无子操作（无 ``program_list``）
- 必须实现 ``t_count()`` 方法
- 必须实现 ``pyqsparse_object()`` 方法

内置原语
--------

门操作
~~~~~~

.. list-table::
   :widths: 30 70

   * - :class:`~pyqres.primitives.gates.Hadamard`
     - Hadamard 门
   * - :class:`~pyqres.primitives.gates.X`
     - Pauli-X 门
   * - :class:`~pyqres.primitives.gates.Y`
     - Pauli-Y 门
   * - :class:`~pyqres.primitives.gates.CNOT`
     - 受控非门
   * - :class:`~pyqres.primitives.gates.Toffoli`
     - Toffoli 门
   * - :class:`~pyqres.primitives.gates.Rx` / :class:`~pyqres.primitives.gates.Ry` / :class:`~pyqres.primitives.gates.Rz`
     - 旋转门

算术操作
~~~~~~~~

.. list-table::
   :widths: 30 70

   * - :class:`~pyqres.primitives.arithmetic.Add_UInt_UInt`
     - 无符号整数加法
   * - :class:`~pyqres.primitives.arithmetic.Add_UInt_ConstUInt`
     - 无符号整数加常数
   * - :class:`~pyqres.primitives.arithmetic.Mult_UInt_ConstUInt`
     - 无符号整数乘常数
   * - :class:`~pyqres.primitives.arithmetic.Compare_UInt_UInt`
     - 无符号整数比较
   * - :class:`~pyqres.primitives.arithmetic.ShiftLeft` / :class:`~pyqres.primitives.arithmetic.ShiftRight`
     - 移位操作

寄存器操作
~~~~~~~~~~

.. list-table::
   :widths: 30 70

   * - :class:`~pyqres.primitives.register_ops.SplitRegister`
     - 拆分寄存器
   * - :class:`~pyqres.primitives.register_ops.CombineRegister`
     - 合并寄存器
   * - :class:`~pyqres.primitives.register_ops.Push` / :class:`~pyqres.primitives.register_ops.Pop`
     - 栈操作