"""Comprehensive tests for mission planner functionality.

Tests mission loading, validation, dry-run, and execution.
"""

import pytest
import json
from pathlib import Path
import tempfile

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

try:
    from mission_runtime import MissionPlanner
    from mission_runtime.schema import MissionConfig
except ImportError:
    pytest.skip("mission_runtime not available", allow_module_level=True)


class TestMissionPlanner:
    """Comprehensive tests for MissionPlanner."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_mission(self, temp_dir):
        """Create a sample mission file."""
        mission_data = {
            "mission_id": "test_mission_001",
            "engine_type": "igsoa",
            "parameters": {
                "num_nodes": 1024,
                "R_c": 1.0,
                "kappa": 1.0,
                "gamma": 0.1,
                "dt": 0.01,
                "num_steps": 100
            },
            "initial_conditions": {
                "profile_type": "gaussian",
                "amplitude": 1.0,
                "sigma": 1.0
            }
        }

        mission_file = temp_dir / "test_mission.json"
        with open(mission_file, 'w') as f:
            json.dump(mission_data, f)

        return mission_file

    @pytest.fixture
    def planner(self, temp_dir):
        """Create a MissionPlanner instance."""
        return MissionPlanner(report_dir=temp_dir)

    def test_load_mission_success(self, planner, sample_mission):
        """Test loading a valid mission file."""
        # Load mission
        mission = planner.load_mission(sample_mission)

        # Verify mission loaded correctly
        assert mission is not None
        assert mission.get("mission_id") == "test_mission_001"
        assert mission.get("engine_type") == "igsoa"
        assert "parameters" in mission
        assert mission["parameters"]["num_nodes"] == 1024

    def test_load_mission_not_found(self, planner, temp_dir):
        """Test loading non-existent mission file."""
        non_existent = temp_dir / "does_not_exist.json"

        with pytest.raises(FileNotFoundError):
            planner.load_mission(non_existent)

    def test_load_mission_invalid_json(self, planner, temp_dir):
        """Test loading invalid JSON file."""
        invalid_file = temp_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            planner.load_mission(invalid_file)

    def test_validate_mission_success(self, planner, sample_mission):
        """Test validation of valid mission."""
        mission = planner.load_mission(sample_mission)
        errors = planner.validate_mission(mission)

        # Should have no errors
        assert len(errors) == 0

    def test_validate_mission_missing_required_field(self, planner, temp_dir):
        """Test validation with missing required field."""
        incomplete_mission = {
            "mission_id": "incomplete_mission",
            # Missing engine_type
            "parameters": {
                "num_nodes": 1024,
            }
        }

        mission_file = temp_dir / "incomplete.json"
        with open(mission_file, 'w') as f:
            json.dump(incomplete_mission, f)

        mission = planner.load_mission(mission_file)
        errors = planner.validate_mission(mission)

        # Should have errors
        assert len(errors) > 0
        assert any("engine_type" in str(err).lower() for err in errors)

    def test_validate_mission_invalid_engine_type(self, planner, temp_dir):
        """Test validation with invalid engine type."""
        invalid_mission = {
            "mission_id": "invalid_engine",
            "engine_type": "nonexistent_engine",
            "parameters": {}
        }

        mission_file = temp_dir / "invalid_engine.json"
        with open(mission_file, 'w') as f:
            json.dump(invalid_mission, f)

        mission = planner.load_mission(mission_file)
        errors = planner.validate_mission(mission)

        # Should have errors about invalid engine
        assert len(errors) > 0

    def test_validate_mission_invalid_parameter_types(self, planner, temp_dir):
        """Test validation with wrong parameter types."""
        invalid_params = {
            "mission_id": "invalid_params",
            "engine_type": "igsoa",
            "parameters": {
                "num_nodes": "not_a_number",  # Should be int
                "R_c": "not_a_float",  # Should be float
                "dt": -0.01,  # Should be positive
            }
        }

        mission_file = temp_dir / "invalid_params.json"
        with open(mission_file, 'w') as f:
            json.dump(invalid_params, f)

        mission = planner.load_mission(mission_file)
        errors = planner.validate_mission(mission)

        # Should have multiple errors
        assert len(errors) >= 2

    def test_validate_mission_parameter_constraints(self, planner, temp_dir):
        """Test validation of parameter constraints."""
        constrained_mission = {
            "mission_id": "constrained",
            "engine_type": "igsoa",
            "parameters": {
                "num_nodes": -100,  # Should be positive
                "R_c": 0.0,  # Should be > 0
                "dt": 0.0,  # Should be > 0
                "num_steps": 0,  # Should be >= 1
            }
        }

        mission_file = temp_dir / "constrained.json"
        with open(mission_file, 'w') as f:
            json.dump(constrained_mission, f)

        mission = planner.load_mission(mission_file)
        errors = planner.validate_mission(mission)

        # Should have multiple constraint violations
        assert len(errors) >= 3

    def test_dry_run_success(self, planner, sample_mission):
        """Test dry-run of valid mission."""
        summary = planner.dry_run(sample_mission)

        # Verify summary
        assert summary is not None
        assert summary.num_commands >= 1
        assert not summary.has_errors
        assert summary.report_path is not None
        assert summary.report_path.exists()

    def test_dry_run_detects_errors(self, planner, temp_dir):
        """Test dry-run detects mission errors."""
        bad_mission = {
            "mission_id": "bad_mission",
            "engine_type": "igsoa",
            "parameters": {
                "num_nodes": 0,  # Invalid
                "dt": 0.0,  # Invalid
                "num_steps": 0,  # Invalid
            }
        }

        mission_file = temp_dir / "bad_mission.json"
        with open(mission_file, 'w') as f:
            json.dump(bad_mission, f)

        summary = planner.dry_run(mission_file)

        # Should detect errors
        assert summary.has_errors
        assert len(summary.issues["errors"]) > 0

    def test_dry_run_generates_report(self, planner, sample_mission):
        """Test dry-run generates report file."""
        summary = planner.dry_run(sample_mission)

        # Verify report exists and contains expected info
        assert summary.report_path.exists()

        report_content = summary.report_path.read_text(encoding="utf-8")
        assert "test_mission_001" in report_content
        assert "generated_at" in report_content or "timestamp" in report_content.lower()

    def test_mission_command_counting(self, planner, temp_dir):
        """Test mission command counting."""
        multi_command_mission = {
            "mission_id": "multi_command",
            "engine_type": "igsoa",
            "commands": [
                {"type": "initialize", "params": {}},
                {"type": "run", "params": {"steps": 100}},
                {"type": "export", "params": {"format": "csv"}},
            ]
        }

        mission_file = temp_dir / "multi_command.json"
        with open(mission_file, 'w') as f:
            json.dump(multi_command_mission, f)

        summary = planner.dry_run(mission_file)

        # Should count commands
        assert summary.num_commands == 3

    def test_mission_command_types(self, planner, temp_dir):
        """Test mission command type tracking."""
        multi_type_mission = {
            "mission_id": "multi_type",
            "engine_type": "igsoa",
            "commands": [
                {"type": "initialize", "params": {}},
                {"type": "run", "params": {"steps": 50}},
                {"type": "run", "params": {"steps": 50}},
                {"type": "export", "params": {}},
            ]
        }

        mission_file = temp_dir / "multi_type.json"
        with open(mission_file, 'w') as f:
            json.dump(multi_type_mission, f)

        summary = planner.dry_run(mission_file)

        # Should track command types
        assert "initialize" in summary.command_counts
        assert summary.command_counts["run"] == 2

    @pytest.mark.parametrize("engine_type", ["dase", "igsoa", "satp"])
    def test_all_engine_types(self, planner, temp_dir, engine_type):
        """Test mission planning for all engine types."""
        mission = {
            "mission_id": f"test_{engine_type}",
            "engine_type": engine_type,
            "parameters": {
                "num_nodes": 1024,
                "dt": 0.01,
                "num_steps": 100,
            }
        }

        mission_file = temp_dir / f"{engine_type}_mission.json"
        with open(mission_file, 'w') as f:
            json.dump(mission, f)

        # Should validate successfully for all engine types
        loaded = planner.load_mission(mission_file)
        assert loaded["engine_type"] == engine_type

    def test_mission_with_complex_initial_conditions(self, planner, temp_dir):
        """Test mission with complex initial conditions."""
        complex_mission = {
            "mission_id": "complex_ic",
            "engine_type": "igsoa",
            "parameters": {
                "num_nodes": 1024,
                "dt": 0.01,
                "num_steps": 100,
            },
            "initial_conditions": {
                "profile_type": "gaussian",
                "amplitude": 1.0,
                "sigma": 1.0,
                "center": [0.0, 0.0],
                "velocity": [0.1, 0.0],
                "phase": 0.5,
            }
        }

        mission_file = temp_dir / "complex_ic.json"
        with open(mission_file, 'w') as f:
            json.dump(complex_mission, f)

        summary = planner.dry_run(mission_file)
        assert not summary.has_errors

    def test_mission_dependency_resolution(self, planner, temp_dir):
        """Test mission command dependency resolution."""
        dependent_mission = {
            "mission_id": "dependent",
            "engine_type": "igsoa",
            "commands": [
                {"type": "initialize", "id": "init1", "params": {}},
                {"type": "run", "id": "run1", "depends_on": ["init1"], "params": {"steps": 50}},
                {"type": "export", "id": "export1", "depends_on": ["run1"], "params": {}},
            ]
        }

        mission_file = temp_dir / "dependent.json"
        with open(mission_file, 'w') as f:
            json.dump(dependent_mission, f)

        summary = planner.dry_run(mission_file)

        # Should resolve dependencies without errors
        assert not summary.has_errors


class TestMissionConfig:
    """Tests for MissionConfig schema validation."""

    def test_minimal_valid_config(self):
        """Test minimal valid configuration."""
        config = MissionConfig(
            mission_id="minimal",
            engine_type="igsoa",
            parameters={
                "num_nodes": 1024,
                "dt": 0.01,
                "num_steps": 100,
            }
        )

        assert config.mission_id == "minimal"
        assert config.engine_type == "igsoa"

    def test_config_with_defaults(self):
        """Test configuration with default values."""
        config = MissionConfig(
            mission_id="with_defaults",
            engine_type="igsoa",
        )

        # Should have default values
        assert hasattr(config, "parameters")

    def test_config_validation_invalid_types(self):
        """Test configuration validation catches type errors."""
        with pytest.raises((TypeError, ValueError)):
            MissionConfig(
                mission_id=123,  # Should be string
                engine_type="igsoa",
            )

    @pytest.mark.parametrize("num_nodes", [0, -1, -100])
    def test_config_validation_positive_constraints(self, num_nodes):
        """Test configuration validation enforces positive constraints."""
        with pytest.raises((ValueError, AssertionError)):
            MissionConfig(
                mission_id="invalid_nodes",
                engine_type="igsoa",
                parameters={"num_nodes": num_nodes}
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
