pyqres.primitives
=================

门操作
------

.. currentmodule:: pyqres.primitives.gates

.. autoclass:: Hadamard
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Hadamard_NDigits
   :show-inheritance:
   :special-members: __init__

.. autoclass:: X
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Y
   :show-inheritance:
   :special-members: __init__

.. autoclass:: CNOT
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Toffoli
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Rx
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Ry
   :show-inheritance:
   :special-members: __init__

.. autoclass:: PhaseGate
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Rz
   :show-inheritance:
   :special-members: __init__

.. autoclass:: U3
   :show-inheritance:
   :special-members: __init__

算术操作
--------

.. currentmodule:: pyqres.primitives.arithmetic

.. autoclass:: Add_UInt_UInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Add_UInt_UInt_InPlace
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Add_UInt_ConstUInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Add_ConstUInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Mult_UInt_ConstUInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: ShiftLeft
   :show-inheritance:
   :special-members: __init__

.. autoclass:: ShiftRight
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Compare_UInt_UInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Less_UInt_UInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: GetMid_UInt_UInt
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Assign
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Swap_General_General
   :show-inheritance:
   :special-members: __init__

寄存器操作
----------

.. currentmodule:: pyqres.primitives.register_ops

.. autoclass:: SplitRegister
   :show-inheritance:
   :special-members: __init__

.. autoclass:: CombineRegister
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Push
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Pop
   :show-inheritance:
   :special-members: __init__

变换操作
--------

.. currentmodule:: pyqres.primitives.transform

.. autoclass:: QFT
   :show-inheritance:
   :special-members: __init__

.. autoclass:: InverseQFT
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Reflection_Bool
   :show-inheritance:
   :special-members: __init__

态制备
------

.. currentmodule:: pyqres.primitives.state_prep

.. autoclass:: Normalize
   :show-inheritance:
   :special-members: __init__

.. autoclass:: ClearZero
   :show-inheritance:
   :special-members: __init__

QRAM
----

.. currentmodule:: pyqres.primitives.qram

.. autoclass:: QRAM
   :show-inheritance:
   :special-members: __init__