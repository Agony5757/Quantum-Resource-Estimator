"""
Quantum-Resource-Estimator Library - Pre-implemented quantum operations.

This package contains reusable quantum operation definitions that can be
imported into user projects without reimplementing common algorithms.

Usage:
    pyqres compile --lib pyqres/lib/arithmetic/
    pyqres compile --lib pyqres/lib/oracles/

Or in YAML:
    imports:
      - pyqres.lib.arithmetic
"""

__all__ = ['arithmetic', 'oracles', 'state_prep']
