# Quantum-Resource-Estimator (pyqres)

量子计算资源估计工具，基于寄存器级编程范式。估算 T-count、T-depth、Toffoli-count、Toffoli-depth，对接 PySparQ C++ 模拟器，支持 Quantikz LaTeX 线路图生成。

## 常用命令

```bash
pip install -e .                  # 开发安装
pytest tests/ -v                  # 运行全部 ~296 个测试
pytest tests/test_simulation.py   # 仅运行 PySparQ 模拟测试（需安装 pysparq，见外部依赖）
pyqres compile                    # 编译 YAML schema → Python 代码
pyqres check                      # 完整性检查（依赖、覆盖率）
pyqres show <operation> --depth 3 # 显示操作依赖树
```

## CI

GitHub Actions (`.github/workflows/ci.yml`)：Python 3.10/3.12 矩阵测试，自动构建 PySparQ C++ 模拟器依赖。测试只需 `pytest tests/ -v`，无需安装 PySparQ（`conftest.py` 自动 mock）。

## 项目架构

```
pyqres/
├── cli.py                          # CLI 入口 (compile/check/show/estimate)
├── core/
│   ├── operation.py                # 核心类层次: Operation/Primitive/Composite/StandardComposite/AbstractComposite
│   ├── metadata.py                 # RegisterMetadata (含 register_types) + ProgramMetadata
│   ├── registry.py                 # OperationRegistry 自动注册
│   ├── primitive_registry.py       # 原语集管理（加载/切换原语集）
│   ├── visitor.py                  # TCounter / TDepthCounter / TreeRenderer / PlainRenderer
│   ├── lowering.py                 # LoweringEngine + ResourceEstimator + SimulationEstimator
│   ├── simulator.py                # SimulatorVisitor 对接 PySparQ (含类型映射)
│   └── utils.py                    # merge_controllers, reg_sz, mcx_t_count 等辅助函数
├── primitives/                     # 手写原语（直接映射 PySparQ 操作）
│   ├── gates.py                    # Hadamard, X, Y, CNOT, Toffoli, Rx, Ry, Rz, Phase, U3 + Phase 2: Hadamard_Bool, Sgate, Tgate, SXgate, U2gate, Swap_Bool_Bool, GlobalPhase
│   ├── arithmetic.py               # Add, Mult, Shift, Compare, Less, GetMid, Assign, Swap_General + Phase 2: Add_Mult_UInt_ConstUInt, GetDataAddr, GetRowAddr, CustomArithmetic, PlusOneAndOverflow
│   ├── register_ops.py             # SplitRegister, CombineRegister, Push, Pop + Phase 2: AddRegister, AddRegisterWithHadamard, RemoveRegister, MoveBackRegister
│   ├── transform.py                # QFT, InverseQFT, Reflection_Bool
│   ├── state_prep.py               # Normalize, ClearZero, Init_Unsafe, Rot_GeneralStatePrep, ViewNormalization
│   ├── qram.py                     # QRAM, QRAMFast（特殊原语）
│   ├── cond_rot.py                 # CondRot_General_Bool, ZeroConditionalPhaseFlip + Phase 2: CondRot_Rational_Bool, Rot_GeneralUnitary
│   ├── measurement.py              # Phase 2: PartialTrace, Prob, StatePrint
│   ├── debug.py                    # DebugPrimitive, CheckNan, CheckNormalization（debug 模式运行，release 模式跳过）
│   └── _utils.py                   # 原语共享工具
├── algorithms/                     # 手写算法（含复杂 sum_t_count 公式）
│   ├── amplitude_amplification.py  # 幅度放大
│   ├── tomography.py               # 量子层析
│   ├── linear_solver.py            # 线性求解器
│   ├── grover.py                   # Grover 搜索 (GroverOracle, DiffusionOperator, GroverSearch, grover_search, grover_count)
│   ├── shor.py                    # Shor 分解 (ModMul, ExpMod, SemiClassicalShor, Shor, factor, factor_full_quantum)
│   ├── block_encoding.py           # 块编码 (BlockEncodingTridiagonal, UR, UL, BlockEncodingViaQRAM, PlusOneOverflow)
│   └── state_prep.py              # QRAM 态制备 (StatePrepViaQRAM, StatePreparation)
├── generated/                      # YAML 自动生成的组合操作类（不要手动编辑）
│   ├── Swap.py                    # DSL: basic.yml
│   ├── GroverSearch.py            # DSL: grover_search.yml（完整 Oracle + Diffusion）
│   └── ShorFactor.py              # DSL: shor_factor.yml（占位符，ExpMod 无法 DSL 表达）
├── lib/                            # 预定义操作库
│   ├── arithmetic/                 # 算术操作库
│   ├── oracles/                    # Oracle 操作库
│   └── state_prep/                 # 态制备库
├── dsl/
│   ├── schema.py                   # YAML schema 数据模型（含 PrimitiveSchemaValidator）
│   ├── compiler.py                 # 编译编排（校验→生成→写文件，支持库加载）
│   ├── codegen.py                  # YAML → Python 代码生成
│   ├── checker.py                  # 依赖分析 & 覆盖率报告
│   └── schemas/
│       ├── primitives/             # 原语集 YAML 定义（.primitive.yaml）
│       ├── composites/             # 组合操作 YAML 定义
│       └── meta/                   # JSON Schema 文件（用于外部工具验证）
└── quantikz/
    └── generator.py                # LaTeX 量子线路图生成 (quantikz2)
```

### 数据流

```
YAML Schema → compiler → codegen → generated/*.py
                                          ↓
                               Operation tree (运行时)
                                          ↓
                    LoweringEngine.estimate(op, estimator)
                                          ↓
                    Visitors: TCounter / TDepthCounter /
                              SimulatorVisitor / TreeRenderer
```

### Operation 类层次

```
Operation (metaclass=OperationMeta, auto-registers to OperationRegistry)
├── Primitive          — 叶节点，直接映射 PySparQ 操作，必须实现 pyqsparse_object() + t_count()
└── Composite          — 通过 program_list 分解为子操作
    ├── StandardComposite — 默认 sum_t_count()（子节点求和）
    └── AbstractComposite — 自定义 sum_t_count()（需覆写）
```

### PySparQ 寄存器类型

算术原语需要正确的寄存器类型，通过 `RegisterMetadata.declare_register(name, size, reg_type)` 指定：

| 类型 | 用途 | PySparQ 映射 |
|------|------|-------------|
| `General` (默认) | 门操作 | `StateStorageType.General` |
| `UnsignedInteger` | 算术操作 | `StateStorageType.UnsignedInteger` |
| `Boolean` | 标志位 (Compare/Less) | `StateStorageType.Boolean` |

## 关键设计决策

- **Visitor 模式**：TCounter、TDepthCounter、SimulatorVisitor、TreeRenderer 都通过 `operation.traverse(visitor)` 遍历
- **Controller 链**：支持 4 种控制类型（nonzero/all_ones/bit/value），通过 `control()` 流式 API 叠加
- **Dagger 传播**：`traverse_children` 中 dagger_ctx 通过 XOR 传播，reversed 遍历子节点
- **self_conjugate 标记**：`__self_conjugate__ = True` 表示 U† = U，dagger 传播在此停止
- **control_override**：用于自定义控制器传播模式（如 Swap 的 cnot_swap）
- **原语集系统**：通过 `.primitive.yaml` 定义原语集，编译时可用 `--primitive` 选择
- **库文件**：预定义操作放在 `pyqres/lib/`，通过 `--lib` 加载
- **自动注册**：`OperationMeta` 元类将所有 Operation 子类注册到 `OperationRegistry`
- **QRAM 是特殊原语**：不做 resource estimation，`t_count()` 返回 0
- **DebugPrimitive**：继承 `Primitive`，`pyqsparse_object()` 在 debug 模式执行 pysparq 操作，`t_count()` 返回 0；子类示例：`CheckNan`、`CheckNormalization`
- **algorithms/ 不迁移 YAML**：含复杂数学表达式，需手写 Python 逻辑（Shor 分解的 ModMul/ExpMod 需要动态循环和 Python callable，超出 DSL 表达能力）
- **DSL for_each range() 语义**：当 `items` 引用 `type: int` 参数时自动包装为 `range()`；引用 `type: array` 参数时直接迭代

## YAML Schema 字段

### 组合操作字段

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `name` | 是 | string | 操作名（PascalCase）|
| `description` | 否 | string | 描述 |
| `qregs` | 否 | array | 量子寄存器声明 |
| `params` | 否 | array | 经典参数声明 |
| `temp_regs` | 否 | array | 临时寄存器 |
| `computed_params` | 否 | array | 计算参数 |
| `impl` | 是 | array | 实现体 |
| `self_conjugate` | 否 | bool | 是否自伴（U† = U），默认 false |
| `control_override` | 否 | string | 控制器传播模式（如 `cnot_swap`）|
| `sum_t_count_formula` | 否 | string | 设为 `custom` 使用 AbstractComposite |

### 原语集字段

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `name` | 是 | string | 原语集名（snake_case）|
| `description` | 否 | string | 描述 |
| `primitives` | 是 | array | 原语操作名列表 |

### DSL for_each / loop 语义

| YAML 字段 | 行为 |
|-----------|------|
| `loop: {iterations: N, body: [...]}` | 生成 `for i in range(N):` — 展开子操作到 program_list |
| `for_each: {var: x, items: [1,2,3], body: [...]}` | 生成 `for x in [1, 2, 3]:` — 字面量列表 |
| `for_each: {var: x, items: n_qubits, body: [...]}` | `type: int` 参数 → `for x in range(self.n_qubits):` |
| `for_each: {var: x, items: angles, body: [...]}` | `type: array` 参数 → `for x in self.angles:` — 直接迭代 |

### DSL 算法覆盖情况

| 算法 | DSL 可表达 | 说明 |
|------|-----------|------|
| Grover 搜索 | ✓ 是 | Oracle（Compare + ZeroConditionalPhaseFlip）+ Diffusion（H^X^MCZX^H）|
| Shor 分解 | ✗ 否 | ModMul 需要 `2**j` 动态幂次；ExpMod 需要 Python callable；必须手写 Python |
| CKS 线性求解 | ✗ 否 | 依赖 Block Encoding + QRAM_Count，DSL 不支持动态循环或 Python callable |
| 幅度放大 | ✓ 部分 | 纯 Python 子类（`amplitude_amplification.py`）含 math 表达式，DSL 可表达框架但 Grover 迭代更直接 |

## 开发约定

- YAML schema 文件放在 `pyqres/dsl/schemas/`，primitives 放 `primitives/`，组合操作放 `composites/`
- 生成的代码写入 `pyqres/generated/`，不要手动编辑（由 `pyqres compile` 生成）
- 新增原语操作：在 `primitives/` 手写类，实现 `pyqsparse_object()` 和 `t_count()`
- 新增组合操作：在 `dsl/schemas/composites/` 添加 YAML，然后运行 `pyqres compile`
- 模拟测试需要安装 pysparq（`pip install git+https://github.com/IAI-USTC-Quantum/QRAM-Simulator.git@main`），其他测试通过 conftest mock 运行
- `t_count()` 返回 `NotImplementedError` 的是占位符，待后续填充

## 外部依赖

- **PySparQ** (`pysparq`)：C++ 量子稀疏态模拟器，从 fork 安装：
  `pip install git+https://github.com/IAI-USTC-Quantum/QRAM-Simulator.git@main`
  CI 自动构建；本地开发非必需（`conftest.py` 自动 mock）
- **quantikz2**：LaTeX 包，生成线路图需系统安装 `pdflatex`
- **运行时依赖**：numpy, lark, sympy, pyyaml

## QRAM-Simulator / PySparQ API 参考

本项目使用 [IAI-USTC-Quantum/QRAM-Simulator](https://github.com/IAI-USTC-Quantum/QRAM-Simulator) 作为 PySparQ C++ 模拟器后端。

### QRAMCircuit_qutrit 构造函数

```python
# 无 memory：单独创建地址和数据寄存器后配合 QRAMLoad 使用
qram = ps.QRAMCircuit_qutrit(addr_size, data_size)

# 带 memory：一步初始化，memory 必须是 Python list/tuple（不接受 numpy array）
qram = ps.QRAMCircuit_qutrit(addr_size, data_size, [i * 2 for i in range(16)])
```

`QRAMLoad(qram, "addr", "data")(state)` 将 `|addr⟩|0⟩ → |addr⟩|memory[addr]⟩`。

### 寄存器级别编程核心操作

```python
state = ps.SparseState()
addr_id = ps.AddRegister("addr", ps.UnsignedInteger, 4)(state)
data_id = ps.AddRegister("data", ps.UnsignedInteger, 8)(state)

# 叠加态（Hadamard 作用于整个寄存器）
ps.Hadamard_Int("addr", 4)(state)

# 打印状态（Detail=1, Binary=2, Prob=4，可 OR 组合）
ps.StatePrint(state, mode=ps.StatePrintDisplay.Detail | ps.StatePrintDisplay.Prob)
```

### 已知 PySparQ API 陷阱

- 单比特 X 门用 `ps.Xgate_Bool(reg, digit)`，不是 `FlipBool`
- 多比特翻转用 `ps.FlipBools(reg)`，参数是寄存器名字符串，不是列表
- 算术操作要求 `UnsignedInteger` 类型寄存器，`General` 类型会抛 ValueError
- Compare/Less 的标志寄存器需要 `Boolean` 类型
- `QRAMCircuit_qutrit(addr_size, data_size, memory)` 中 `memory` 必须是 Python `list`/`tuple`，不接受 numpy array（C++ 层抛出 `ValueError: Invalid input`）
- pysparq `cks_solver.cks_solve`（已 deprecated）使用 `QRAMCircuit_qutrit` 有 C++ fatal error；测试改用 `cks_solve_v2`（推荐版本，古典 fallback）
