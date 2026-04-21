# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Phase 6 - 文档完善**:
  - CLI estimate 命令文档（t_count/t_depth/toffoli_count 三种指标）
  - Toffoli-count 估计文档页面
- **Phase 5 - Resource Estimation**:
  - T-count formulas for all primitives (Y gate, controlled rotations, arithmetic, QFT, etc.)
  - T-depth estimation via default `t_depth()` in Primitive class
  - ToffoliCounter visitor and ToffoliCountEstimator
  - `pyqres estimate` CLI command for computing T-count/T-depth/Toffoli-count
  - Resource estimation tests (21 new tests)
- End-to-end simulation tests (40+ tests covering all primitives)
- QuantikzVisitor for LaTeX circuit generation
- New primitives: Init_Unsafe, Rot_GeneralStatePrep, Div_Sqrt_Arccos_Int_Int, Sqrt_Div_Arccos_Int_Int, GetRotateAngle_Int_Int
- SimulationEstimator in lowering engine
- Register type tracking in RegisterMetadata (General, UnsignedInteger, SignedInteger, Boolean, Rational)

### Fixed
- `sync_t_depth` and `get_depth` functions now handle empty/integer cases correctly
- SimulatorVisitor: added verbose parameter, removed hardcoded StatePrint
- X/CNOT/Toffoli gates: FlipBool → Xgate_Bool (correct PySparQ API)
- CNOT/Toffoli: FlipBools now takes string, not list
- Toffoli: fixed wrong attribute name (control_qubit_index → control_qubit_index1)
- SimulatorVisitor: registers now use correct StateStorageType based on type metadata

### Changed
- Architecture refactoring: Operation/Primitive/Composite class hierarchy
- All documentation updated to reflect new class names and file paths
- Test count: 139 tests passing

### Closed
- GitHub Issue #1 (DSL Infrastructure Implementation Tracking) — 所有 DSL 功能已完成
