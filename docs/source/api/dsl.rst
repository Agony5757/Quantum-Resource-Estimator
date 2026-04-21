pyqres.dsl
==========

Schema 校验
-----------

.. currentmodule:: pyqres.dsl.schema

SchemaValidator
~~~~~~~~~~~~~~~

.. autoclass:: SchemaValidator
   :members:
   :special-members: __init__

ValidationError
~~~~~~~~~~~~~~~

.. autoexception:: ValidationError

.. autofunction:: validate_yaml_definitions

代码生成
--------

.. currentmodule:: pyqres.dsl.codegen

CodeGenerator
~~~~~~~~~~~~~

.. autoclass:: CodeGenerator
   :members:
   :special-members: __init__

GeneratedClass
~~~~~~~~~~~~~~

.. autoclass:: GeneratedClass
   :members:
   :special-members: __init__

.. autofunction:: generate_class

编译器
------

.. currentmodule:: pyqres.dsl.compiler

DSLCompiler
~~~~~~~~~~~

.. autoclass:: DSLCompiler
   :members:
   :special-members: __init__

CompilationError
~~~~~~~~~~~~~~~~

.. autoexception:: CompilationError

.. autofunction:: compile_yaml

.. autofunction:: compile_all_schemas

完整性检查
----------

.. currentmodule:: pyqres.dsl.checker

CompletenessChecker
~~~~~~~~~~~~~~~~~~~

.. autoclass:: CompletenessChecker
   :members:
   :special-members: __init__

CompletenessReport
~~~~~~~~~~~~~~~~~~

.. autoclass:: CompletenessReport
   :members:
   :special-members: __init__

DependencyNode
~~~~~~~~~~~~~~

.. autoclass:: DependencyNode
   :members:
   :special-members: __init__

.. autofunction:: check_completeness

.. autofunction:: check_directory