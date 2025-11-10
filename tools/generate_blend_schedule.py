import json
import sys

def generate_linear_schedule(start, end, cycles):
    step = (end - start) / (cycles - 1)
    return [round(start + i * step, 6) for i in range(cycles)]

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/generate_blend_schedule.py schedule.json")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        cfg = json.load(f)

    sch = cfg.get("blend_weight_function", {})
    if sch.get("type") != "linear":
        print("ERROR: Only type:'linear' supported in this helper version.")
        sys.exit(1)

    start = float(sch["start"])
    end = float(sch["end"])
    cycles = int(sch["cycles"])

    weights = generate_linear_schedule(start, end, cycles)

    print("== SATP v2 Generated blend schedule ==")
    for i,w in enumerate(weights, start=1):
        print(f"cycle {i}: blend_weight = {w}")

    print("\nPaste directly into SATP_v2 mission file.\n")

if __name__ == "__main__":
    main()
