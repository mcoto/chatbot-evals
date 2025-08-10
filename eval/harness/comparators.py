# eval/harness/comparators.py
from __future__ import annotations
import re
from typing import Any, Optional

def _get_path(data: Any, path: str) -> Any:
    """
    Navega un dict/list siguiendo rutas tipo "a.b.c" o "a.b[0].c".
    """
    cur = data
    for part in path.split("."):
        idx = None
        if "[" in part and part.endswith("]"):
            part, idx = part[:-1].split("[", 1)
            idx = int(idx)
        if part:
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        if idx is not None:
            if not isinstance(cur, list) or idx >= len(cur):
                return None
            cur = cur[idx]
    return cur

def equals(left: Any, right: Any) -> bool:
    return left == right

def approx_equals(left: Any, right: Any, abs_tol: float = 0.0) -> bool:
    try:
        return abs(float(left) - float(right)) <= abs_tol
    except Exception:
        return False

def not_null(value: Any) -> bool:
    return value is not None

def regex(value: Any, pattern: str) -> bool:
    if value is None:
        return False
    return re.search(pattern, str(value)) is not None

def contains(haystack: Any, needle: str) -> bool:
    if haystack is None:
        return False
    return needle.lower() in str(haystack).lower()

def eval_condition(truth: dict, response: dict, condition: str) -> bool:
    """
    Condición muy simple tipo: "truth.order.status == 'delayed'"
    Soporta truth.* y response.*  (response.* espera dict con keys 'text' y 'json')
    """
    safe = {"__builtins__": {}}
    ctx = {"truth": truth, "response": response}
    try:
        return bool(eval(condition, safe, ctx))
    except Exception:
        return False

def get_from(data_bag: dict, dotted: str) -> Any:
    return _get_path(data_bag, dotted)

