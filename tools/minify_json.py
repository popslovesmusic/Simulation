#!/usr/bin/env python3
"""
Minify JSON files - convert pretty-printed JSON to single-line format
Usage: python minify_json.py input.json output.json
"""
import json
import sys

if len(sys.argv) != 3:
    print("Usage: python minify_json.py input.json output.json")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    with open(input_file, 'r') as f:
        data = json.load(f)

    with open(output_file, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

    print(f"✅ Converted {input_file} -> {output_file}")

except json.JSONDecodeError as e:
    print(f"❌ JSON parse error: {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"❌ File not found: {input_file}")
    sys.exit(1)
