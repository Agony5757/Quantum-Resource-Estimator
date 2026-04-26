"""Test fixtures for pyqres tests."""

import pytest

from pyqres.core.metadata import RegisterMetadata


@pytest.fixture(autouse=True)
def clean_metadata():
    """Clean register metadata between tests."""
    while len(RegisterMetadata.register_metadata_stack) > 1:
        RegisterMetadata.pop_register_metadata()
    RegisterMetadata.register_metadata_stack.clear()
    RegisterMetadata.push_register_metadata()
    yield
    while len(RegisterMetadata.register_metadata_stack) > 0:
        RegisterMetadata.pop_register_metadata()
    RegisterMetadata.push_register_metadata()


def declare_regs(**regs):
    for name, size in regs.items():
        RegisterMetadata.get_register_metadata().declare_register(name, size)


def declare_regs_typed(*entries):
    for entry in entries:
        if len(entry) == 3:
            name, size, rtype = entry
        else:
            name, size = entry
            rtype = "General"
        RegisterMetadata.get_register_metadata().declare_register(name, size, rtype)
