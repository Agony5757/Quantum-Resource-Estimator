"""
CLI interface for Quantum-Resource-Estimator DSL commands.

Commands:
    pyqres compile   - Compile YAML definitions to Python
    pyqres check     - Check completeness of definitions
    pyqres show      - Show dependency tree for an operation
    pyqres estimate  - Estimate resources for an operation
"""

import argparse
import sys
from pathlib import Path
import yaml


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='pyqres',
        description='Quantum-Resource-Estimator DSL tools for quantum resource estimation'
    )

    subparsers = parser.add_subparsers(dest='command', help='DSL commands')

    # Compile command
    compile_parser = subparsers.add_parser(
        'compile',
        help='Compile YAML composite definitions to Python classes'
    )
    compile_parser.add_argument(
        '--source', '-s',
        type=str,
        default=None,
        help='Source YAML file or directory (default: dsl/schemas/)'
    )
    compile_parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output directory for generated Python files'
    )
    compile_parser.add_argument(
        '--primitive',
        type=str,
        default=None,
        help='Primitive set to use (e.g., clifford_t, toffoli, qram)'
    )
    compile_parser.add_argument(
        '--lib',
        type=str,
        action='append',
        default=None,
        help='Library directory to load (can be specified multiple times)'
    )

    # Check command
    check_parser = subparsers.add_parser(
        'check',
        help='Check completeness of composite definitions'
    )
    check_parser.add_argument(
        '--source', '-s',
        type=str,
        default=None,
        help='Source YAML file or directory'
    )

    # Show command
    show_parser = subparsers.add_parser(
        'show',
        help='Show dependency tree for an operation'
    )
    show_parser.add_argument(
        'operation',
        type=str,
        help='Operation name to show'
    )
    show_parser.add_argument(
        '--source', '-s',
        type=str,
        default=None,
        help='Source YAML directory'
    )
    show_parser.add_argument(
        '--depth', '-d',
        type=int,
        default=10,
        help='Maximum tree depth'
    )

    # Estimate command
    estimate_parser = subparsers.add_parser(
        'estimate',
        help='Estimate resources for an operation'
    )
    estimate_parser.add_argument(
        'operation',
        type=str,
        help='Operation name to estimate'
    )
    estimate_parser.add_argument(
        '--registers', '-r',
        type=str,
        default='',
        help='Registers as "name:size,name:size,..." (default: q0:1,q1:1,q2:1)'
    )
    estimate_parser.add_argument(
        '--params', '-p',
        type=str,
        default='',
        help='Parameters as "name:value,name:value,..."'
    )
    estimate_parser.add_argument(
        '--metric', '-m',
        type=str,
        choices=['t_count', 't_depth', 'toffoli_count'],
        default='t_count',
        help='Resource metric to compute (default: t_count)'
    )
    estimate_parser.add_argument(
        '--primitive',
        type=str,
        default=None,
        help='Primitive set to use for lowering (e.g., clifford_t, toffoli)'
    )

    return parser


def cmd_compile(args):
    """Execute compile command."""
    # Ensure primitives are loaded first
    import pyqres.primitives  # noqa: F401

    from pyqres.dsl.compiler import DSLCompiler, CompilationError
    from pyqres.core.primitive_registry import PrimitiveRegistry

    # Load primitive sets
    prim_dir = Path(__file__).parent / "dsl" / "schemas" / "primitives"
    if prim_dir.exists():
        PrimitiveRegistry.load_from_directory(str(prim_dir))

    # Set active primitive set if specified
    if args.primitive:
        try:
            PrimitiveRegistry.set_active(args.primitive)
        except Exception as e:
            print(f"Error setting primitive set: {e}")
            return 1

    # Create compiler with library paths
    compiler = DSLCompiler(library_paths=args.lib)

    source = args.source
    output = args.output

    # Default paths
    if source is None:
        source = Path(__file__).parent / "dsl" / "schemas"
    else:
        source = Path(source)

    if output is None:
        output = Path(__file__).parent / "generated"
    else:
        output = Path(output)

    try:
        if source.is_file():
            results = compiler.compile_file(str(source), str(output))
            print(f"Compiled {len(results)} operations from {source}")
        elif source.is_dir():
            results = compiler.compile_all(str(source), str(output))
            print(f"Compiled {len(results)} operations from {source}")
        else:
            print(f"Error: Source not found: {source}")
            return 1

        for warning in compiler.warnings:
            print(f"Warning: {warning}")

    except CompilationError as e:
        print(f"Compilation failed:\n{e}")
        return 1

    return 0


def cmd_check(args):
    """Execute check command."""
    # Ensure primitives are loaded first
    import pyqres.primitives  # noqa: F401

    from pyqres.dsl.checker import CompletenessChecker

    checker = CompletenessChecker()

    source = args.source
    if source is None:
        source = Path(__file__).parent / "dsl" / "schemas"
    else:
        source = Path(source)

    if source.is_file():
        with open(source) as f:
            definitions = yaml.safe_load(f)
        if definitions is None:
            definitions = []
        if not isinstance(definitions, list):
            definitions = [definitions]
        checker.add_definitions(definitions)
    elif source.is_dir():
        checker.load_from_directory(str(source))
    else:
        print(f"Error: Source not found: {source}")
        return 1

    report = checker.check()
    print(report)

    if not report.is_valid:
        return 1

    return 0


def cmd_show(args):
    """Execute show command."""
    # Ensure primitives are loaded first
    import pyqres.primitives  # noqa: F401

    from pyqres.dsl.checker import CompletenessChecker

    checker = CompletenessChecker()

    source = args.source
    if source is None:
        source = Path(__file__).parent / "dsl" / "schemas"
    else:
        source = Path(source)

    if source.is_dir():
        checker.load_from_directory(str(source))
    else:
        print(f"Error: Source directory not found: {source}")
        return 1

    tree = checker.get_tree(args.operation, depth=0, max_depth=args.depth)
    print(f"Dependency tree for {args.operation}:")
    print(tree)

    return 0


def cmd_estimate(args):
    """Execute estimate command."""
    # Ensure primitives are loaded first
    import pyqres.primitives  # noqa: F401

    from pyqres.core.registry import OperationRegistry
    from pyqres.core.metadata import RegisterMetadata
    from pyqres.core.lowering import (
        LoweringEngine, TCountEstimator, TDepthEstimator, ToffoliCountEstimator
    )
    from pyqres.core.primitive_registry import PrimitiveRegistry

    # Load primitive sets
    prim_dir = Path(__file__).parent / "dsl" / "schemas" / "primitives"
    if prim_dir.exists():
        PrimitiveRegistry.load_from_directory(str(prim_dir))

    # Set active primitive set if specified
    if args.primitive:
        try:
            PrimitiveRegistry.set_active(args.primitive)
        except Exception as e:
            print(f"Error setting primitive set: {e}")
            return 1

    # Get operation class
    if not OperationRegistry.has_class(args.operation):
        print(f"Error: Operation '{args.operation}' not found in registry")
        print(f"Available operations: {', '.join(sorted(OperationRegistry.list_classes()))}")
        return 1

    op_cls = OperationRegistry.get_class(args.operation)

    # Parse registers
    registers = {}
    if args.registers:
        for reg_def in args.registers.split(','):
            if ':' in reg_def:
                name, size = reg_def.split(':')
                registers[name] = int(size)
    if not registers:
        registers = {'q0': 1, 'q1': 1, 'q2': 1}

    # Parse parameters
    params = []
    if args.params:
        param_dict = {}
        for param_def in args.params.split(','):
            if ':' in param_def:
                name, value = param_def.split(':')
                # Try to convert to number
                try:
                    value = float(value)
                    if value.is_integer():
                        value = int(value)
                except ValueError:
                    pass
                param_dict[name] = value
        # Convert dict to list (sorted by name for consistency)
        params = [param_dict[k] for k in sorted(param_dict.keys())]

    # Set up register metadata
    RegisterMetadata.push_register_metadata()
    try:
        rm = RegisterMetadata.get_register_metadata()
        for name, size in registers.items():
            rm.declare_register(name, size)

        # Create operation instance
        reg_list = list(registers.keys())
        try:
            op = op_cls(reg_list, params if params else None)
        except TypeError as e:
            print(f"Error creating operation instance: {e}")
            print(f"Operation: {args.operation}")
            print(f"Registers: {reg_list}")
            print(f"Parameters: {params}")
            return 1

        # Estimate resources
        engine = LoweringEngine()
        if args.metric == 't_count':
            estimator = TCountEstimator()
            result = engine.estimate(op, estimator)
        elif args.metric == 't_depth':
            estimator = TDepthEstimator()
            result = engine.estimate(op, estimator)
        elif args.metric == 'toffoli_count':
            estimator = ToffoliCountEstimator()
            result = engine.estimate(op, estimator)

        print(f"Operation: {args.operation}")
        print(f"Registers: {registers}")
        print(f"Parameters: {params if params else 'none'}")
        print(f"{estimator.name}: {result}")

    finally:
        RegisterMetadata.pop_register_metadata()

    return 0


def main(argv=None):
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == 'compile':
        return cmd_compile(args)
    elif args.command == 'check':
        return cmd_check(args)
    elif args.command == 'show':
        return cmd_show(args)
    elif args.command == 'estimate':
        return cmd_estimate(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
