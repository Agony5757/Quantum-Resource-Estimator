"""Tests for the DSL system (schema, codegen, compiler, checker)."""

import pytest
from pathlib import Path

from pyqres.dsl.schema import SchemaValidator, ValidationError
from pyqres.dsl.codegen import CodeGenerator, GeneratedClass
from pyqres.dsl.compiler import DSLCompiler, CompilationError
from pyqres.dsl.checker import CompletenessChecker, CompletenessReport

# Ensure primitives are loaded
import pyqres.primitives  # noqa: F401


class TestSchemaValidator:
    def test_valid_composite(self):
        defn = {
            "name": "MyOp",
            "qregs": [{"name": "r1", "type": "General"}, {"name": "r2", "type": "General"}],
            "impl": [{"op": "CNOT", "qregs": ["r1", "r2"]}],
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"CNOT"})
        assert errors == []

    def test_missing_name(self):
        defn = {"impl": [{"op": "CNOT"}]}
        validator = SchemaValidator()
        errors = validator.validate([defn])
        assert len(errors) > 0
        assert any("name" in str(e).lower() for e in errors)

    def test_missing_impl(self):
        defn = {"name": "NoImpl", "qregs": [{"name": "r1", "type": "General"}]}
        validator = SchemaValidator()
        errors = validator.validate([defn])
        assert len(errors) > 0
        assert any("impl" in str(e).lower() for e in errors)

    def test_invalid_register_type(self):
        defn = {
            "name": "BadReg",
            "qregs": [{"name": "r1", "type": "InvalidType"}],
            "impl": [{"op": "CNOT", "qregs": ["r1"]}],
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"CNOT"})
        assert any("Invalid register type" in str(e) for e in errors)

    def test_unknown_op_reference(self):
        defn = {
            "name": "UsesUnknown",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "NonExistentOp", "qregs": ["r1"]}],
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"CNOT"})
        assert any("unknown operation" in str(e).lower() for e in errors)

    def test_valid_controllers(self):
        defn = {
            "name": "CtrlOp",
            "qregs": [{"name": "r1", "type": "General"}, {"name": "r2", "type": "General"}],
            "impl": [{"op": "CNOT", "qregs": ["r1", "r2"], "controllers": {"all_ones": ["r1"]}}],
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"CNOT"})
        assert errors == []

    def test_invalid_controller_type(self):
        defn = {
            "name": "BadCtrl",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "CNOT", "qregs": ["r1"], "controllers": {"invalid": ["r1"]}}],
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"CNOT"})
        assert any("Invalid controller" in str(e) for e in errors)


class TestCodeGenerator:
    def test_generate_composite(self):
        defn = {
            "name": "MySwap",
            "qregs": [{"name": "r1", "type": "General"}, {"name": "r2", "type": "General"}],
            "impl": [
                {"op": "CNOT", "qregs": ["r1", "r2"]},
                {"op": "CNOT", "qregs": ["r2", "r1"]},
            ],
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        assert result.name == "MySwap"
        assert result.base_class == "StandardComposite"
        assert "CNOT" in result.dependencies

    def test_generate_file_content(self):
        defn = {
            "name": "SimpleOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}],
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "class SimpleOp(StandardComposite):" in content
        assert "OperationRegistry" in content

    def test_control_override(self):
        defn = {
            "name": "CnotSwap",
            "qregs": [{"name": "r1", "type": "General"}, {"name": "r2", "type": "General"}],
            "impl": [
                {"op": "CNOT", "qregs": ["r1", "r2"]},
                {"op": "CNOT", "qregs": ["r2", "r1"]},
                {"op": "CNOT", "qregs": ["r1", "r2"]},
            ],
            "control_override": "cnot_swap",
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "traverse_children" in content

    def test_dagger_in_impl(self):
        defn = {
            "name": "DagOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"], "dagger": True}],
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert ".dagger()" in content

    def test_self_conjugate_generation(self):
        defn = {
            "name": "SelfConjOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}],
            "self_conjugate": True,
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "__self_conjugate__ = True" in content


class TestSelfConjugateValidation:
    """Tests for self_conjugate validation."""

    def test_valid_self_conjugate_true(self):
        defn = {
            "name": "SelfConjOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}],
            "self_conjugate": True,
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard"})
        assert errors == []

    def test_valid_self_conjugate_false(self):
        defn = {
            "name": "NotSelfConjOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Rx", "qregs": ["r1"]}],
            "self_conjugate": False,
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Rx"})
        assert errors == []

    def test_invalid_self_conjugate_type(self):
        defn = {
            "name": "BadSelfConj",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}],
            "self_conjugate": "yes",
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard"})
        assert any("self_conjugate" in str(e) for e in errors)


class TestDSLCompiler:
    def test_compile_file(self, tmp_path):
        yaml_content = """
- name: MyOp
  qregs:
    - {name: r1, type: General}
  impl:
    - op: Hadamard
      qregs: [r1]
"""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)

        output_dir = tmp_path / "output"
        compiler = DSLCompiler()
        results = compiler.compile_file(str(yaml_file), str(output_dir))
        assert len(results) == 1
        assert results[0].name == "MyOp"

    def test_compile_invalid_yaml(self, tmp_path):
        yaml_content = """
- name: MissingImpl
  qregs:
    - {name: r1, type: General}
"""
        yaml_file = tmp_path / "bad.yml"
        yaml_file.write_text(yaml_content)

        compiler = DSLCompiler()
        with pytest.raises(CompilationError):
            compiler.compile_file(str(yaml_file))


class TestCompletenessChecker:
    def test_all_defined(self):
        defn = {
            "name": "UsesCNOT",
            "qregs": [{"name": "r1", "type": "General"}, {"name": "r2", "type": "General"}],
            "impl": [{"op": "CNOT", "qregs": ["r1", "r2"]}],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn])
        report = checker.check()
        assert report.is_valid

    def test_missing_operations(self):
        defn = {
            "name": "UsesUnknown",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "NonExistentOp", "qregs": ["r1"]}],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn])
        report = checker.check()
        assert not report.is_valid
        assert "NonExistentOp" in report.missing_operations

    def test_cycle_detection(self):
        defn_a = {
            "name": "OpA",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "OpB", "qregs": ["r1"]}],
        }
        defn_b = {
            "name": "OpB",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "OpA", "qregs": ["r1"]}],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn_a, defn_b])
        report = checker.check()
        assert len(report.circular_dependencies) > 0

    def test_dependency_order(self):
        defn_leaf = {
            "name": "LeafOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "CNOT", "qregs": ["r1"]}],
        }
        defn_mid = {
            "name": "MidOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "LeafOp", "qregs": ["r1"]}],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn_leaf, defn_mid])
        order = checker.get_dependency_order()
        assert order.index("LeafOp") < order.index("MidOp")

    def test_get_tree(self):
        defn = {
            "name": "UsesH",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn])
        tree = checker.get_tree("UsesH")
        assert "UsesH" in tree
        assert "Hadamard" in tree

    def test_schema_directory(self):
        schema_dir = Path(__file__).parent.parent / "pyqres" / "dsl" / "schemas"
        if schema_dir.exists():
            checker = CompletenessChecker()
            checker.load_from_directory(str(schema_dir))
            report = checker.check()
            assert report.is_valid

    def test_nested_dependencies_in_loop(self):
        """Test that dependencies are extracted from nested loop bodies."""
        defn = {
            "name": "NestedLoop",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"loop": {"iterations": 3, "body": [
                    {"op": "Hadamard", "qregs": ["r1"]}
                ]}}
            ],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn])
        report = checker.check()
        assert report.is_valid
        # Hadamard should be recognized as a dependency from nested loop
        assert "Hadamard" in checker.graph["NestedLoop"].dependencies

    def test_nested_dependencies_in_if(self):
        """Test that dependencies are extracted from if/else bodies."""
        defn = {
            "name": "ConditionalOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "flag", "type": "bool"}],
            "impl": [
                {"if": {
                    "condition": "self.flag",
                    "body": [{"op": "Hadamard", "qregs": ["r1"]}],
                    "else": [{"op": "X", "qregs": ["r1"]}]
                }}
            ],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn])
        report = checker.check()
        assert report.is_valid
        # Both Hadamard and X should be recognized as dependencies
        deps = checker.graph["ConditionalOp"].dependencies
        assert "Hadamard" in deps
        assert "X" in deps

    def test_nested_dependencies_in_for_each(self):
        """Test that dependencies are extracted from for_each bodies."""
        defn = {
            "name": "ForEachOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"for_each": {
                    "var": "angle",
                    "items": [0.1, 0.2, 0.3],
                    "body": [{"op": "PhaseGate", "qregs": ["r1"], "params": ["$angle", 0.01]}]
                }}
            ],
        }
        checker = CompletenessChecker()
        checker.add_definitions([defn])
        report = checker.check()
        assert report.is_valid
        assert "PhaseGate" in checker.graph["ForEachOp"].dependencies


class TestIfElseValidation:
    """Tests for if/else/elif validation."""

    def test_valid_if_else(self):
        defn = {
            "name": "IfElseOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "mode", "type": "int"}],
            "impl": [{
                "if": {
                    "condition": "self.mode == 1",
                    "body": [{"op": "Hadamard", "qregs": ["r1"]}],
                    "else": [{"op": "X", "qregs": ["r1"]}]
                }
            }]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard", "X"})
        assert errors == []

    def test_valid_if_elif_else(self):
        defn = {
            "name": "IfElifOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "mode", "type": "int"}],
            "impl": [{
                "if": {
                    "condition": "self.mode == 1",
                    "body": [{"op": "Hadamard", "qregs": ["r1"]}],
                    "elif": [{
                        "condition": "self.mode == 2",
                        "body": [{"op": "X", "qregs": ["r1"]}]
                    }],
                    "else": [{"op": "Y", "qregs": ["r1"]}]
                }
            }]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard", "X", "Y"})
        assert errors == []

    def test_if_missing_condition(self):
        defn = {
            "name": "BadIf",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{
                "if": {
                    "body": [{"op": "Hadamard", "qregs": ["r1"]}]
                }
            }]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard"})
        assert any("condition" in str(e).lower() for e in errors)


class TestForEachValidation:
    """Tests for for_each validation."""

    def test_valid_for_each_literal(self):
        defn = {
            "name": "ForEachLiteral",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{
                "for_each": {
                    "var": "angle",
                    "items": [0.1, 0.2, 0.3],
                    "body": [{"op": "PhaseGate", "qregs": ["r1"], "params": ["$angle", 0.01]}]
                }
            }]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"PhaseGate"})
        assert errors == []

    def test_for_each_missing_var(self):
        defn = {
            "name": "BadForEach",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{
                "for_each": {
                    "items": [1, 2, 3],
                    "body": [{"op": "X", "qregs": ["r1"]}]
                }
            }]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"X"})
        assert any("var" in str(e).lower() for e in errors)

    def test_for_each_missing_items(self):
        defn = {
            "name": "BadForEach2",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{
                "for_each": {
                    "var": "i",
                    "body": [{"op": "X", "qregs": ["r1"]}]
                }
            }]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"X"})
        assert any("items" in str(e).lower() for e in errors)


class TestIfElseCodeGen:
    """Tests for if/else/elif code generation."""

    def test_generate_if_else(self):
        defn = {
            "name": "IfElseGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "flag", "type": "bool"}],
            "impl": [{
                "if": {
                    "condition": "self.flag",
                    "body": [{"op": "Hadamard", "qregs": ["r1"]}],
                    "else": [{"op": "X", "qregs": ["r1"]}]
                }
            }]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "if self.flag:" in content
        assert "else:" in content
        assert "Hadamard" in content
        assert '"X"' in content

    def test_generate_if_elif_else(self):
        defn = {
            "name": "IfElifGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "mode", "type": "int"}],
            "impl": [{
                "if": {
                    "condition": "self.mode == 1",
                    "body": [{"op": "Hadamard", "qregs": ["r1"]}],
                    "elif": [{
                        "condition": "self.mode == 2",
                        "body": [{"op": "X", "qregs": ["r1"]}]
                    }],
                    "else": [{"op": "Y", "qregs": ["r1"]}]
                }
            }]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "if self.mode == 1:" in content
        assert "elif self.mode == 2:" in content
        assert "else:" in content


class TestForEachCodeGen:
    """Tests for for_each code generation."""

    def test_generate_for_each_literal(self):
        defn = {
            "name": "ForEachLiteralGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [{
                "for_each": {
                    "var": "i",
                    "items": [1, 2, 3],
                    "body": [{"op": "PhaseGate", "qregs": ["r1"], "params": ["$i", 0.01]}]
                }
            }]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "for i in [1, 2, 3]:" in content
        assert "PhaseGate" in content

    def test_generate_for_each_param_ref(self):
        defn = {
            "name": "ForEachParamGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "angles", "type": "array"}],
            "impl": [{
                "for_each": {
                    "var": "angle",
                    "items": "angles",
                    "body": [{"op": "PhaseGate", "qregs": ["r1"], "params": ["$angle", 0.01]}]
                }
            }]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "for angle in self.angles:" in content
        # $angle should be replaced with angle (not self.angle)
        assert "param_list=[angle, 0.01]" in content


class TestStrTypeValidation:
    """Tests for str type parameter validation."""

    def test_valid_str_param(self):
        defn = {
            "name": "StrParamOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "mode", "type": "str"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard"})
        assert errors == []

    def test_str_param_generation(self):
        defn = {
            "name": "StrParamGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [{"name": "unitary_name", "type": "str"}],
            "impl": [{"op": "Hadamard", "qregs": ["r1"]}]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "self.unitary_name = param_list[0]" in content


class TestNestedControlFlow:
    """Tests for nested control flow structures."""

    def test_nested_loop_if_for_each(self):
        """Test nested control structures."""
        defn = {
            "name": "NestedControl",
            "qregs": [{"name": "r1", "type": "General"}],
            "params": [
                {"name": "n", "type": "int"},
                {"name": "modes", "type": "array"}
            ],
            "impl": [
                {"loop": {"iterations": "n", "body": [
                    {"for_each": {"var": "mode", "items": "modes", "body": [
                        {"if": {"condition": "mode == 'h'", "body": [
                            {"op": "Hadamard", "qregs": ["r1"]}
                        ], "else": [
                            {"op": "X", "qregs": ["r1"]}
                        ]}}
                    ]}}
                ]}}
            ]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "for i in range(self.n):" in content
        assert "for mode in self.modes:" in content
        assert "if mode == 'h':" in content


class TestPythonBlock:
    """Tests for python code block."""

    def test_valid_python_block(self):
        """Test that python blocks pass validation."""
        defn = {
            "name": "PythonOp",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"python": "self.program_list.append(OperationRegistry.get_class('Hadamard')(reg_list=[self.r1]))"}
            ]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn])
        assert errors == []

    def test_python_block_multiline(self):
        """Test that multiline python blocks pass validation."""
        defn = {
            "name": "MultilinePython",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"python": "for i in range(3):\n    self.program_list.append(OperationRegistry.get_class('X')(reg_list=[self.r1]))"}
            ]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn])
        assert errors == []

    def test_python_block_codegen(self):
        """Test that python blocks generate correct code."""
        defn = {
            "name": "PythonGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"python": "self.program_list.append(OperationRegistry.get_class('Hadamard')(reg_list=[self.r1]))"}
            ]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "self.program_list.append(OperationRegistry.get_class('Hadamard')(reg_list=[self.r1]))" in content

    def test_python_block_multiline_codegen(self):
        """Test that multiline python blocks generate correctly."""
        defn = {
            "name": "MultilinePythonGen",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"python": "for i in range(3):\n    self.program_list.append(OperationRegistry.get_class('X')(reg_list=[self.r1]))"}
            ]
        }
        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "for i in range(3):" in content
        assert "self.program_list.append(OperationRegistry.get_class('X')(reg_list=[self.r1]))" in content

    def test_python_block_with_ops(self):
        """Test python block mixed with normal ops."""
        defn = {
            "name": "MixedPython",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"op": "Hadamard", "qregs": ["r1"]},
                {"python": "# Custom logic here\nself._custom_flag = True"},
                {"op": "X", "qregs": ["r1"]},
            ]
        }
        validator = SchemaValidator()
        errors = validator.validate([defn], known_operations={"Hadamard", "X"})
        assert errors == []

        gen = CodeGenerator()
        result = gen.generate(defn)
        content = gen.generate_file_content(result)
        assert "# Custom logic here" in content
        assert "self._custom_flag = True" in content

    def test_python_block_no_dependencies(self):
        """Test that python blocks don't add dependencies."""
        defn = {
            "name": "PythonNoDep",
            "qregs": [{"name": "r1", "type": "General"}],
            "impl": [
                {"python": "self._do_something()"}
            ]
        }
        checker = CompletenessChecker()
        checker.add_definition(defn)
        report = checker.check()
        # Should be valid - no missing operations
        assert report.is_valid
        # No dependencies should be extracted
        assert len(checker.graph["PythonNoDep"].dependencies) == 0
