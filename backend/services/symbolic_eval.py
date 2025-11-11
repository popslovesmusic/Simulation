"""SymPy-backed sandbox evaluator used by the Command Center playground.

The script reads a JSON payload from ``stdin`` with the following schema::

    {
        "expression": "sin(x)**2 + cos(x)**2",
        "variables": {"x": 0.5},
        "operations": ["simplify", "evalf"],
        "assumptions": {"x": {"real": true}}
    }

It returns a JSON object on ``stdout`` documenting the simplified
expression, optional numeric evaluation, LaTeX output and any errors.

By keeping the interface file-based the Node.js API can safely spawn
this script without importing SymPy into the JavaScript runtime.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover - availability guard
    json.dump({
        "status": "error",
        "error": f"SymPy is required for symbolic evaluation: {exc}"
    }, sys.stdout)
    sys.exit(0)


@dataclass
class EvaluationRequest:
    expression: str
    variables: Mapping[str, Any]
    operations: List[str]
    assumptions: Mapping[str, Mapping[str, bool]]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "EvaluationRequest":
        expression = str(payload.get("expression", "")).strip()
        if not expression:
            raise ValueError("expression is required")
        variables = payload.get("variables") or {}
        operations_input: Iterable[str] = payload.get("operations") or ["simplify", "evalf"]
        operations = [str(op) for op in operations_input]
        assumptions = payload.get("assumptions") or {}
        return cls(expression, variables, operations, assumptions)


SAFE_FUNCTIONS: Dict[str, Any] = {
    name: getattr(sp, name)
    for name in [
        "sin", "cos", "tan", "sqrt", "log", "exp", "pi", "E", "Symbol", "symbols",
        "Matrix", "diff", "integrate", "simplify", "factor", "expand", "Abs"
    ]
}
SAFE_FUNCTIONS.update({"ln": sp.log, "pow": sp.Pow})


def _build_symbols(variables: Mapping[str, Any], assumptions: Mapping[str, Mapping[str, bool]]) -> Dict[str, sp.Symbol]:
    symbols: Dict[str, sp.Symbol] = {}
    for name in set(list(variables.keys()) + list(assumptions.keys())):
        kwargs = assumptions.get(name, {})
        symbols[name] = sp.symbols(name, **{k: bool(v) for k, v in kwargs.items()})
    return symbols


def evaluate(request: EvaluationRequest) -> Dict[str, Any]:
    symbols = _build_symbols(request.variables, request.assumptions)
    locals_dict = {**SAFE_FUNCTIONS, **symbols}

    expression = sp.sympify(request.expression, locals=locals_dict)
    result: Dict[str, Any] = {
        "input": request.expression,
        "repr": sp.srepr(expression),
        "latex": sp.latex(expression),
    }

    if "simplify" in request.operations:
        simplified = sp.simplify(expression)
        result["simplified"] = {
            "expr": sp.srepr(simplified),
            "latex": sp.latex(simplified),
            "text": sp.sstr(simplified),
        }
        expression = simplified

    if "diff" in request.operations:
        variable_name = next(iter(request.variables.keys() or []), None)
        if variable_name and variable_name in symbols:
            derivative = sp.diff(expression, symbols[variable_name])
            result["derivative"] = {
                "expr": sp.srepr(derivative),
                "latex": sp.latex(derivative),
                "text": sp.sstr(derivative),
            }

    if "integrate" in request.operations:
        variable_name = next(iter(request.variables.keys() or []), None)
        if variable_name and variable_name in symbols:
            integral = sp.integrate(expression, symbols[variable_name])
            result["integral"] = {
                "expr": sp.srepr(integral),
                "latex": sp.latex(integral),
                "text": sp.sstr(integral),
            }

    if "evalf" in request.operations:
        substitutions = {symbols[name]: value for name, value in request.variables.items() if name in symbols}
        if substitutions:
            numeric = expression.evalf(subs=substitutions)
        else:
            numeric = expression.evalf()
        if numeric.is_real:
            numeric_value: Any = float(numeric)
        else:
            numeric_value = complex(numeric)
        if isinstance(numeric_value, complex) and math.isclose(numeric_value.imag, 0, abs_tol=1e-12):
            numeric_value = float(numeric_value.real)
        result["numeric"] = numeric_value

    return result


def main() -> None:
    try:
        payload = sys.stdin.read() or "{}"
        data = json.loads(payload)
        request = EvaluationRequest.from_payload(data)
        outcome = evaluate(request)
        json.dump({"status": "ok", "result": outcome, "operations": list(request.operations)}, sys.stdout)
    except Exception as exc:  # pragma: no cover - defensive wrapper
        json.dump({"status": "error", "error": str(exc)}, sys.stdout)


if __name__ == "__main__":
    main()
