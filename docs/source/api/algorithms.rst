pyqres.algorithms
=================

幅度放大
--------

.. currentmodule:: pyqres.algorithms.amplitude_amplification

.. autoclass:: AmplitudeAmplification
   :members:
   :show-inheritance:
   :special-members: __init__

量子层析
--------

.. currentmodule:: pyqres.algorithms.tomography

.. autoclass:: Tomography
   :members:
   :show-inheritance:
   :special-members: __init__

线性求解器
----------

.. currentmodule:: pyqres.algorithms.linear_solver

.. autoclass:: LinearSolver
   :members:
   :show-inheritance:
   :special-members: __init__

Grover 搜索
-----------

.. currentmodule:: pyqres.algorithms.grover

.. autoclass:: GroverOracle
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: DiffusionOperator
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: GroverOperator
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: GroverSearch
   :members:
   :show-inheritance:
   :special-members: __init__

.. autofunction:: grover_search

.. autofunction:: grover_count

Shor 分解
----------

.. currentmodule:: pyqres.algorithms.shor

.. autoclass:: ModMul
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: ExpMod
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: SemiClassicalShor
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: Shor
   :members:
   :show-inheritance:
   :special-members: __init__

.. autofunction:: factor

.. autofunction:: factor_full_quantum

.. autofunction:: general_expmod

.. autofunction:: shor_postprocess

块编码
------

.. currentmodule:: pyqres.algorithms.block_encoding

.. autofunction:: get_tridiagonal_matrix

.. autofunction:: get_u_plus

.. autofunction:: get_u_minus

.. autoclass:: BlockEncodingTridiagonal
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: UR
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: UL
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: BlockEncodingViaQRAM
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: PlusOneOverflow
   :members:
   :show-inheritance:
   :special-members: __init__

QRAM 态制备
-----------

.. currentmodule:: pyqres.algorithms.state_prep

.. autofunction:: pow2

.. autofunction:: get_complement

.. autofunction:: make_complement

.. autofunction:: make_vector_tree

.. autofunction:: make_func

.. autofunction:: make_func_inv

.. autoclass:: StatePrepViaQRAM
   :members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: StatePreparation
   :members:
   :special-members: __init__
