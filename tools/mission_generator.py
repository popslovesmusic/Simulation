#!/usr/bin/env python3
"""
IGSOA-SIM Mission Generator
Generates properly formatted mission files for dase_cli.exe

Usage:
  python mission_generator.py --template gaussian --output missions/my_mission.json
  python mission_generator.py --interactive
  python mission_generator.py --rc-sweep 0.1 2.0 5 --output missions/rc_sweep/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


class MissionGenerator:
    """Generate IGSOA mission files with proper newline-delimited JSON format"""

    def __init__(self):
        self.commands = []

    def add_command(self, command: str, params: Dict[str, Any]):
        """Add a command to the mission"""
        self.commands.append({
            "command": command,
            "params": params
        })

    def create_engine(self, engine_type="igsoa_complex", num_nodes=4096,
                     R_c=0.5, include_psi=True, **kwargs):
        """Add create_engine command"""
        params = {
            "engine_type": engine_type,
            "num_nodes": num_nodes,
            "R_c": R_c,
            "include_psi": include_psi
        }
        params.update(kwargs)
        self.add_command("create_engine", params)

    def set_gaussian_state(self, engine_id="engine_001", amplitude=1.5,
                          center_node=2048, width=256):
        """Add Gaussian initial state"""
        self.add_command("set_igsoa_state", {
            "engine_id": engine_id,
            "profile_type": "gaussian",
            "params": {
                "amplitude": amplitude,
                "center_node": center_node,
                "width": width
            }
        })

    def set_soliton_state(self, engine_id="engine_001", amplitude=1.0,
                         center_node=2048, width=100):
        """Add soliton initial state"""
        self.add_command("set_igsoa_state", {
            "engine_id": engine_id,
            "profile_type": "soliton",
            "params": {
                "amplitude": amplitude,
                "center_node": center_node,
                "width": width
            }
        })

    def set_plane_wave_state(self, engine_id="engine_001", amplitude=1.0,
                            wavelength=512):
        """Add plane wave initial state"""
        self.add_command("set_igsoa_state", {
            "engine_id": engine_id,
            "profile_type": "plane_wave",
            "params": {
                "amplitude": amplitude,
                "wavelength": wavelength
            }
        })

    def run_mission(self, engine_id="engine_001", num_steps=50,
                   iterations_per_node=30):
        """Add run_mission command"""
        self.add_command("run_mission", {
            "engine_id": engine_id,
            "num_steps": num_steps,
            "iterations_per_node": iterations_per_node
        })

    def get_state(self, engine_id="engine_001"):
        """Add get_state command"""
        self.add_command("get_state", {
            "engine_id": engine_id
        })

    def destroy_engine(self, engine_id="engine_001"):
        """Add destroy_engine command"""
        self.add_command("destroy_engine", {
            "engine_id": engine_id
        })

    def to_json_lines(self) -> str:
        """Convert to newline-delimited JSON format (one command per line)"""
        return '\n'.join(json.dumps(cmd, separators=(',', ':')) for cmd in self.commands)

    def save(self, filepath: Path):
        """Save mission to file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(self.to_json_lines())
        print(f"✓ Mission saved to: {filepath}")

    def clear(self):
        """Clear all commands"""
        self.commands = []


# ============================================================================
# Mission Templates
# ============================================================================

def template_gaussian(R_c=0.5, num_nodes=4096, num_steps=50,
                     amplitude=1.5, center_node=None, width=256):
    """Gaussian pulse propagation"""
    if center_node is None:
        center_node = num_nodes // 2

    mission = MissionGenerator()
    mission.create_engine(num_nodes=num_nodes, R_c=R_c, include_psi=True)
    mission.set_gaussian_state(amplitude=amplitude, center_node=center_node, width=width)
    mission.run_mission(num_steps=num_steps, iterations_per_node=30)
    mission.get_state()
    mission.destroy_engine()
    return mission


def template_soliton(R_c=0.5, num_nodes=4096, num_steps=100,
                    amplitude=1.0, center_node=None, width=100):
    """Soliton propagation"""
    if center_node is None:
        center_node = num_nodes // 2

    mission = MissionGenerator()
    mission.create_engine(num_nodes=num_nodes, R_c=R_c, include_psi=True)
    mission.set_soliton_state(amplitude=amplitude, center_node=center_node, width=width)
    mission.run_mission(num_steps=num_steps, iterations_per_node=50)
    mission.get_state()
    mission.destroy_engine()
    return mission


def template_plane_wave(R_c=0.5, num_nodes=4096, num_steps=50,
                       amplitude=1.0, wavelength=512):
    """Plane wave propagation"""
    mission = MissionGenerator()
    mission.create_engine(num_nodes=num_nodes, R_c=R_c, include_psi=True)
    mission.set_plane_wave_state(amplitude=amplitude, wavelength=wavelength)
    mission.run_mission(num_steps=num_steps, iterations_per_node=30)
    mission.get_state()
    mission.destroy_engine()
    return mission


def template_rc_sweep(R_c_min=0.1, R_c_max=2.0, num_points=5,
                     num_nodes=4096, num_steps=50):
    """Generate multiple missions sweeping R_c parameter"""
    import numpy as np

    R_c_values = np.linspace(R_c_min, R_c_max, num_points)
    missions = []

    for R_c in R_c_values:
        mission = template_gaussian(R_c=R_c, num_nodes=num_nodes, num_steps=num_steps)
        missions.append((f"mission_rc_{R_c:.1f}.json", mission))

    return missions


def template_2d_gaussian(R_c=0.5, N_x=64, N_y=64, num_steps=50):
    """2D Gaussian pulse"""
    mission = MissionGenerator()
    mission.create_engine(
        engine_type="igsoa_complex_2d",
        dimension_x=N_x,
        dimension_y=N_y,
        R_c=R_c,
        include_psi=True
    )
    mission.add_command("set_igsoa_2d_state", {
        "engine_id": "engine_001",
        "profile_type": "gaussian",
        "params": {
            "amplitude": 1.5,
            "center_x": N_x // 2,
            "center_y": N_y // 2,
            "width_x": 8,
            "width_y": 8
        }
    })
    mission.run_mission(num_steps=num_steps, iterations_per_node=30)
    mission.get_state()
    mission.destroy_engine()
    return mission


# ============================================================================
# Interactive Mode
# ============================================================================

def interactive_mode():
    """Interactive mission builder"""
    print("\n" + "=" * 60)
    print("  IGSOA Mission Generator - Interactive Mode")
    print("=" * 60 + "\n")

    mission = MissionGenerator()

    # Engine setup
    print("Engine Configuration:")
    engine_type = input("  Engine type [igsoa_complex]: ").strip() or "igsoa_complex"
    num_nodes = int(input("  Number of nodes [4096]: ").strip() or "4096")
    R_c = float(input("  R_c value [0.5]: ").strip() or "0.5")

    mission.create_engine(engine_type=engine_type, num_nodes=num_nodes, R_c=R_c)
    print("  ✓ Engine created\n")

    # Initial state
    print("Initial State:")
    print("  1. Gaussian")
    print("  2. Soliton")
    print("  3. Plane wave")
    state_choice = input("  Choice [1]: ").strip() or "1"

    if state_choice == "1":
        amplitude = float(input("  Amplitude [1.5]: ").strip() or "1.5")
        center = int(input(f"  Center node [{num_nodes//2}]: ").strip() or str(num_nodes//2))
        width = int(input("  Width [256]: ").strip() or "256")
        mission.set_gaussian_state(amplitude=amplitude, center_node=center, width=width)
    elif state_choice == "2":
        amplitude = float(input("  Amplitude [1.0]: ").strip() or "1.0")
        center = int(input(f"  Center node [{num_nodes//2}]: ").strip() or str(num_nodes//2))
        width = int(input("  Width [100]: ").strip() or "100")
        mission.set_soliton_state(amplitude=amplitude, center_node=center, width=width)
    else:
        amplitude = float(input("  Amplitude [1.0]: ").strip() or "1.0")
        wavelength = int(input("  Wavelength [512]: ").strip() or "512")
        mission.set_plane_wave_state(amplitude=amplitude, wavelength=wavelength)

    print("  ✓ Initial state configured\n")

    # Simulation parameters
    print("Simulation Parameters:")
    num_steps = int(input("  Number of steps [50]: ").strip() or "50")
    iterations = int(input("  Iterations per node [30]: ").strip() or "30")
    mission.run_mission(num_steps=num_steps, iterations_per_node=iterations)
    print("  ✓ Simulation configured\n")

    # Finalize
    mission.get_state()
    mission.destroy_engine()

    # Save
    print("Save Mission:")
    output = input("  Output file [missions/my_mission.json]: ").strip() or "missions/my_mission.json"
    mission.save(Path(output))

    print("\n✓ Mission generated successfully!")
    print(f"\nRun with:")
    print(f"  cat {output} | dase_cli/dase_cli.exe")


# ============================================================================
# Main CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="IGSOA Mission Generator - Create properly formatted mission files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Templates:
  gaussian     - Gaussian pulse propagation (default)
  soliton      - Soliton propagation
  plane_wave   - Plane wave propagation
  2d_gaussian  - 2D Gaussian pulse

Examples:
  # Generate Gaussian mission
  python mission_generator.py --template gaussian --rc 0.5 --output missions/test.json

  # Generate R_c sweep (multiple files)
  python mission_generator.py --rc-sweep 0.1 2.0 5 --output missions/rc_sweep/

  # Interactive mode
  python mission_generator.py --interactive

  # 2D Gaussian
  python mission_generator.py --template 2d_gaussian --output missions/test_2d.json
        """
    )

    parser.add_argument("--template", "-t",
                       choices=["gaussian", "soliton", "plane_wave", "2d_gaussian"],
                       default="gaussian",
                       help="Mission template to use")

    parser.add_argument("--output", "-o", type=str,
                       help="Output file path")

    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Interactive mode")

    # Engine parameters
    parser.add_argument("--rc", type=float, default=0.5,
                       help="R_c value (default: 0.5)")
    parser.add_argument("--nodes", "-n", type=int, default=4096,
                       help="Number of nodes (default: 4096)")
    parser.add_argument("--steps", "-s", type=int, default=50,
                       help="Number of simulation steps (default: 50)")

    # Initial state parameters
    parser.add_argument("--amplitude", "-a", type=float, default=1.5,
                       help="Initial amplitude (default: 1.5)")
    parser.add_argument("--width", "-w", type=int, default=256,
                       help="Initial width (default: 256)")
    parser.add_argument("--center", "-c", type=int,
                       help="Center node (default: N/2)")

    # R_c sweep mode
    parser.add_argument("--rc-sweep", nargs=3, metavar=("MIN", "MAX", "POINTS"),
                       help="Generate R_c sweep: min max num_points")

    args = parser.parse_args()

    # Interactive mode
    if args.interactive:
        interactive_mode()
        return 0

    # R_c sweep mode
    if args.rc_sweep:
        R_c_min = float(args.rc_sweep[0])
        R_c_max = float(args.rc_sweep[1])
        num_points = int(args.rc_sweep[2])

        if not args.output:
            print("Error: --output directory required for R_c sweep")
            return 1

        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        missions = template_rc_sweep(R_c_min, R_c_max, num_points,
                                     num_nodes=args.nodes, num_steps=args.steps)

        print(f"\nGenerating {len(missions)} missions for R_c sweep...")
        for filename, mission in missions:
            mission.save(output_dir / filename)

        print(f"\n✓ Generated {len(missions)} missions in {output_dir}/")
        print(f"\nRun with:")
        print(f"  for f in {output_dir}/*.json; do cat $f | dase_cli/dase_cli.exe > ${{f%.json}}_output.json; done")
        return 0

    # Template mode
    if args.template == "gaussian":
        mission = template_gaussian(
            R_c=args.rc,
            num_nodes=args.nodes,
            num_steps=args.steps,
            amplitude=args.amplitude,
            center_node=args.center,
            width=args.width
        )
    elif args.template == "soliton":
        mission = template_soliton(
            R_c=args.rc,
            num_nodes=args.nodes,
            num_steps=args.steps,
            amplitude=args.amplitude,
            center_node=args.center,
            width=args.width
        )
    elif args.template == "plane_wave":
        mission = template_plane_wave(
            R_c=args.rc,
            num_nodes=args.nodes,
            num_steps=args.steps,
            amplitude=args.amplitude,
            wavelength=args.width  # Reuse width param for wavelength
        )
    elif args.template == "2d_gaussian":
        N = int(args.nodes ** 0.5)  # Assume square grid
        mission = template_2d_gaussian(
            R_c=args.rc,
            N_x=N,
            N_y=N,
            num_steps=args.steps
        )

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"missions/mission_{args.template}_rc_{args.rc}.json")

    # Save mission
    mission.save(output_path)

    print(f"\nRun with:")
    print(f"  cat {output_path} | dase_cli/dase_cli.exe")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
