"""Tests for CLI commands."""

import pytest
from pathlib import Path

from pyqres.cli import main

# Ensure primitives are loaded
import pyqres.primitives  # noqa: F401


class TestCLI:
    def test_compile_default(self, tmp_path):
        """Test that pyqres compile works with default schema directory."""
        # Just run it and check it doesn't crash
        result = main(["compile"])
        assert result == 0

    def test_check_default(self):
        """Test that pyqres check works with default schema directory."""
        result = main(["check"])
        assert result == 0

    def test_compile_with_source(self, tmp_path):
        """Test compiling a specific YAML file."""
        yaml_content = """
- name: TestOp
  qregs:
    - {name: r1, type: General}
  impl:
    - op: Hadamard
      qregs: [r1]
"""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        output_dir = tmp_path / "output"

        result = main(["compile", "--source", str(yaml_file), "--output", str(output_dir)])
        assert result == 0

    def test_compile_nonexistent_source(self):
        """Test that compiling nonexistent file returns error."""
        result = main(["compile", "--source", "/nonexistent/path.yml"])
        assert result == 1

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        result = main([])
        assert result == 0
