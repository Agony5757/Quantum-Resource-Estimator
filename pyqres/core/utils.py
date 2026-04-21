from copy import deepcopy
from typing import Dict, List, Tuple, Union


def merge_controllers(controller1, controller2):
    """Merge controller2 into controller1, returning a new dict."""
    controller_ret = deepcopy(controller1)
    for control_type, control_list in controller2.items():
        if control_type not in controller_ret:
            controller_ret[control_type] = []
        controller_ret[control_type].extend(control_list)
    return controller_ret


def controller2str(controller):
    parts = []
    for control_type, control_list in controller.items():
        if control_type == 'conditioned_by_nonzero':
            parts.append(f"conditioned_by_nonzero({', '.join(control_list)})")
        elif control_type == 'conditioned_by_all_ones':
            parts.append(f"conditioned_by_all_ones({', '.join(control_list)})")
        elif control_type == 'conditioned_by_bit':
            parts.append(f"conditioned_by_bit({', '.join(f'{reg}[{bit}]' for reg, bit in control_list)})")
        elif control_type == 'conditioned_by_value':
            parts.append(f"conditioned_by_value({', '.join(f'{reg}=={value}' for reg, value in control_list)})")
        else:
            raise ValueError(f"Unknown control type {control_type}")
    return ", ".join(parts)


def reg_sz(reg_name):
    from .metadata import RegisterMetadata
    register_metadata = RegisterMetadata.get_register_metadata()
    reginfo = register_metadata.registers.get(reg_name)
    if reginfo is None:
        raise ValueError(f"Register {reg_name} not declared")
    return reginfo


def get_control_qubit_count(controllers):
    from .metadata import RegisterMetadata
    count = 0
    for control_type, control_list in controllers.items():
        if control_type == 'conditioned_by_bit':
            count += len(control_list)
        elif control_type == 'conditioned_by_value':
            count += sum(reg_sz(cp[0]) for cp in control_list)
        elif control_type in ('conditioned_by_nonzero', 'conditioned_by_all_ones'):
            count += sum(reg_sz(cr) for cr in control_list)
    return count


def mcx_t_count(ncontrols):
    """T-count for multi-controlled X gate."""
    if ncontrols <= 1:
        return 0
    if ncontrols == 2:
        return 7
    return 16 * 7 * ncontrols
