安装
====

系统要求
--------

- Python 3.10+
- pip 包管理器

从源码安装
----------

.. code-block:: bash

   git clone https://github.com/Agony5757/Quantum-Resource-Estimator.git
   cd Quantum-Resource-Estimator
   pip install -e .

开发安装
--------

如需运行测试或开发：

.. code-block:: bash

   pip install -e ".[test,dev]"

验证安装
--------

.. code-block:: python

   import pyqres
   # 导出核心类
   from pyqres import Operation, Primitive, Composite
   from pyqres import TCounter, TDepthCounter