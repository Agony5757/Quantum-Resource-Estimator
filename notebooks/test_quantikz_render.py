import os
import string
import random
from sympy import Symbol
from pathlib import Path

from pyqres import quantikz


def random_registers(n: int) -> dict:
    """生成随机寄存器配置"""
    registers = {}
    used_names = set()
    
    for _ in range(n):
        # 生成唯一名称
        while True:
            name = random.choice(string.ascii_lowercase)
            if name not in used_names:
                used_names.add(name)
                break
        
        # 随机选择寄存器大小类型（固定数值或符号）
        if random.random() < 0.3:  # 30%概率使用符号大小
            size = Symbol(f'n_{name}')
        else:
            size = random.randint(1, 4)
        
        registers[name] = size
    return registers

def random_operation(circuit: quantikz.QuantumCircuit, all_regs: list[str]) -> quantikz.OpCode:
    """生成随机量子操作"""
    # 随机选择目标寄存器（1-3个）
    n_targets = random.randint(1, min(3, len(all_regs)))
    targets = random.sample(all_regs, n_targets)
    
    # 随机选择控制寄存器（0-2个），排除目标寄存器
    possible_controls = [r for r in all_regs if r not in targets]
    n_controls = random.randint(0, min(2, len(possible_controls)))
    controls = random.sample(possible_controls, n_controls) if possible_controls else []
    
    quantikz_controllers = list()
    if controls:
        for control in controls:
            # 生成control_type
            control_type = random.choice(["conditioned_by_nonzero",
                                        "conditioned_by_all_ones",
                                        "conditioned_by_bit",
                                        "conditioned_by_value"])
            
            if control_type == "conditioned_by_bit":
                control_info = random.choice([0, 1, 2])
            elif control_type == "conditioned_by_value":
                control_info = random.choice([0, 1, 2, 3, 4, 5, 6, 7])
            else:
                control_info = None
            
            quantikz_controllers.append(quantikz.Controller(control, control_type, control_info))
    
    # 生成随机参数（0-3个）
    params = []
    for _ in range(random.randint(0, 3)):
        if random.random() < 0.5:
            params.append(random.uniform(0, 10))
        else:
            params.append(Symbol(f'\\theta_{random.choice(string.ascii_lowercase)}'))
    
    return quantikz.OpCode(
        name="Gate",
        targets=targets,
        controls=quantikz_controllers,
        params=params
    )

def run_random_test(n_registers=5, n_gates=20, seed=42):
    """执行随机化测试"""
    random.seed(seed)
    print(f"Running test with {n_registers} registers and {n_gates} gates...")
    
    # 生成随机寄存器配置
    reg_config = random_registers(n_registers)
    circuit = quantikz.QuantumCircuit(reg_config)
    all_regs = list(circuit.registers.keys())
    
    # 添加随机操作
    for _ in range(n_gates):
        op = random_operation(circuit, all_regs)
        circuit.add_op(op)
    
    # 生成LaTeX代码
    try:
        latex_code = quantikz.LatexGenerator.generate(circuit)
        print("LaTeX generation successful!")
        return latex_code
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print("Generated code:")
        print(latex_code)
        return None

def stress_test(
    test_cases = [
        (3, 10),    # 少量寄存器/门
        (5, 50),    # 中等规模
        (10, 10),  # 大规模
        (1, 5),     # 单个寄存器
        (2, 20)     # 两个寄存器高强度
    ], 
    n_trials=3):
    """压力测试：运行多组随机测试"""
        
    os.makedirs("tex_outputs", exist_ok=True)
    path = Path("tex_outputs")

    for n_reg, n_gate in test_cases:
        print(f"\n=== Testing {n_reg} registers with {n_gate} gates ===")
        for seed in range(n_trials):  # 每个配置运行3次不同随机种子            
            print(f"--- Run {seed+1} ---")            
            latex_code = run_random_test(n_reg, n_gate, seed=seed)
            if not latex_code:
                return False
            
            filename = f"test_output_{n_reg}_{n_gate}_{seed}.tex"
            quantikz.Compiler.compile(latex_code, filename)
    
    return True

if __name__ == "__main__":
    # 快速测试
    # run_random_test()
    
    # 完整压力测试
    final_latex_code = stress_test()
    if final_latex_code:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed!")