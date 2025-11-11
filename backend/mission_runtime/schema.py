"""Mission schema validation utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence


class MissionSchemaError(ValueError):
    """Raised when mission data cannot be parsed or validated."""


@dataclass
class MissionValidationResult:
    """Container describing the outcome of mission schema validation."""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    command_counts: Dict[str, int] = field(default_factory=dict)
    physics_ranges: Dict[str, Dict[str, float]] = field(default_factory=dict)
    engine_ids: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Return ``True`` when no blocking validation errors were produced."""

        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the validation result for persistence or reporting."""

        return {
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "command_counts": dict(self.command_counts),
            "physics_ranges": {
                key: dict(value) for key, value in self.physics_ranges.items()
            },
            "engine_ids": list(self.engine_ids),
        }


class MissionSchemaValidator:
    """Validate mission command streams against the runtime contract."""

    _COMMAND_SPECS: Mapping[str, Mapping[str, Any]] = {
        "create_engine": {
            "required": {
                "engine_type": str,
                "num_nodes": int,
            },
            "optional": {
                "R_c": (int, float),
                "include_psi": bool,
            },
        },
        "set_igsoa_state": {
            "required": {
                "engine_id": str,
                "profile_type": str,
                "params": dict,
            },
            "optional": {
                "mode": str,
            },
        },
        "run_mission": {
            "required": {
                "engine_id": str,
                "num_steps": int,
                "iterations_per_node": int,
            },
            "optional": {
                "stabilise_after": int,
            },
        },
        "get_state": {
            "required": {
                "engine_id": str,
            },
            "optional": {
                "output_file": str,
            },
        },
        "destroy_engine": {
            "required": {
                "engine_id": str,
            }
        },
    }

    _PHYSICS_KEYS: Mapping[str, str] = {
        "R_c": "create_engine",
        "num_nodes": "create_engine",
        "num_steps": "run_mission",
        "iterations_per_node": "run_mission",
    }

    def load_from_file(self, mission_path: Path) -> List[Mapping[str, Any]]:
        """Load a mission definition from ``mission_path``.

        Mission files are expected to contain either a JSON array of commands or
        a series of newline-delimited JSON objects.
        """

        if not mission_path.exists():
            raise MissionSchemaError(f"Mission file not found: {mission_path}")

        text = mission_path.read_text(encoding="utf-8").strip()
        if not text:
            raise MissionSchemaError(f"Mission file is empty: {mission_path}")

        # Try to parse as a JSON document first.
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, Mapping):
            return [parsed]
        if isinstance(parsed, Sequence):
            return list(parsed)

        commands: List[Mapping[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                command = json.loads(raw)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
                raise MissionSchemaError(
                    f"Invalid JSON object on line {line_number} of {mission_path}: {exc}"
                ) from exc
            if not isinstance(command, Mapping):
                raise MissionSchemaError(
                    f"Command on line {line_number} is not an object: {command!r}"
                )
            commands.append(command)

        if not commands:
            raise MissionSchemaError(
                f"No commands were parsed from mission file: {mission_path}"
            )
        return commands

    def validate(self, mission: Sequence[Mapping[str, Any]]) -> MissionValidationResult:
        """Validate ``mission`` and collect physics metadata."""

        result = MissionValidationResult()
        physics_values: Dict[str, List[float]] = {key: [] for key in self._PHYSICS_KEYS}
        engine_ids: List[str] = []

        if not isinstance(mission, Sequence):
            raise MissionSchemaError(
                "Mission must be a sequence of command dictionaries."
            )

        for index, command in enumerate(mission):
            location = f"command[{index}]"
            if not isinstance(command, Mapping):
                result.errors.append(f"{location} is not an object")
                continue

            cmd_name = command.get("command")
            if not isinstance(cmd_name, str) or not cmd_name:
                result.errors.append(f"{location} missing 'command' string")
                continue

            params = command.get("params")
            if not isinstance(params, MutableMapping):
                result.errors.append(f"{location} missing 'params' object")
                continue

            result.command_counts[cmd_name] = result.command_counts.get(cmd_name, 0) + 1

            spec = self._COMMAND_SPECS.get(cmd_name)
            if spec is None:
                result.warnings.append(
                    f"{location} uses unrecognised command '{cmd_name}'"
                )
                continue

            for key, expected_type in spec.get("required", {}).items():
                if key not in params:
                    result.errors.append(
                        f"{location}.{cmd_name} missing required parameter '{key}'"
                    )
                    continue
                if not isinstance(params[key], expected_type):
                    result.errors.append(
                        f"{location}.{cmd_name} parameter '{key}' should be {expected_type}"
                    )
                    continue

                self._collect_physics_value(cmd_name, key, params[key], physics_values, result)

            for key, expected_type in spec.get("optional", {}).items():
                if key not in params:
                    continue
                if not isinstance(params[key], expected_type):
                    result.warnings.append(
                        f"{location}.{cmd_name} optional parameter '{key}' should be {expected_type}"
                    )
                    continue
                self._collect_physics_value(cmd_name, key, params[key], physics_values, result)

            engine_id = params.get("engine_id")
            if isinstance(engine_id, str) and engine_id:
                engine_ids.append(engine_id)

            self._validate_physics_constraints(cmd_name, params, location, result)

        result.engine_ids = sorted(set(engine_ids))
        result.physics_ranges = {
            key: {
                "min": float(min(values)),
                "max": float(max(values)),
                "avg": float(sum(values) / len(values)),
            }
            for key, values in physics_values.items()
            if values
        }
        return result

    def _collect_physics_value(
        self,
        command_name: str,
        key: str,
        value: Any,
        physics_values: Dict[str, List[float]],
        result: MissionValidationResult,
    ) -> None:
        target_command = self._PHYSICS_KEYS.get(key)
        if target_command != command_name:
            return

        if isinstance(value, bool):  # bool is subclass of int; ignore explicit booleans
            return
        if isinstance(value, (int, float)):
            physics_values.setdefault(key, []).append(float(value))
        else:
            result.warnings.append(
                f"Parameter '{key}' from '{command_name}' is not numeric: {value!r}"
            )

    def _validate_physics_constraints(
        self,
        command_name: str,
        params: Mapping[str, Any],
        location: str,
        result: MissionValidationResult,
    ) -> None:
        if command_name == "create_engine":
            num_nodes = params.get("num_nodes")
            if isinstance(num_nodes, int) and num_nodes <= 0:
                result.errors.append(
                    f"{location}.create_engine 'num_nodes' must be positive"
                )
            R_c = params.get("R_c")
            if R_c is not None and isinstance(R_c, (int, float)) and R_c <= 0:
                result.errors.append(
                    f"{location}.create_engine 'R_c' must be positive"
                )
        elif command_name == "run_mission":
            for field_name in ("num_steps", "iterations_per_node"):
                value = params.get(field_name)
                if isinstance(value, int) and value <= 0:
                    result.errors.append(
                        f"{location}.run_mission '{field_name}' must be positive"
                    )

