from typing import Callable, Dict
import operator

OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    "lt": operator.lt,
    "le": operator.le,
    "eq": operator.eq,
    "ge": operator.ge,
    "gt": operator.gt
}


class RuleEvaluator(object):
    """
    Atomic component to evaluate a single rule
    """

    @staticmethod
    def is_triggered(current_value: float, operator_str: str, threshold: float) -> bool:
        op_func = OPERATORS.get(operator_str)
        if not op_func:
            return False
        
        return op_func(current_value, threshold)
