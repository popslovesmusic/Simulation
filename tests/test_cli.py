#!/usr/bin/env python3
"""
Test script for DASE CLI
Demonstrates JSON-based communication
"""

import subprocess
import json
import sys

def test_cli_basic():
    """Test basic CLI communication"""
    print("=" * 60)
    print("DASE CLI Test - Basic Communication")
    print("=" * 60)

    try:
        # Start CLI process
        print("\n1. Starting dase_cli process...")
        proc = subprocess.Popen(
            ['dase_cli.exe'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Send test command
        test_command = {
            "command": "test",
            "params": {
                "message": "Hello from AI agent!"
            }
        }

        print(f"\n2. Sending command:")
        print(f"   {json.dumps(test_command, indent=2)}")

        # Write command to stdin
        proc.stdin.write(json.dumps(test_command) + '\n')
        proc.stdin.flush()

        # Read response from stdout
        print("\n3. Waiting for response...")
        response_line = proc.stdout.readline()

        if response_line:
            response = json.loads(response_line)
            print(f"\n4. Response received:")
            print(f"   {json.dumps(response, indent=2)}")

            # Check status
            if response.get("status") == "success":
                print("\n✅ SUCCESS: CLI is working!")
                print(f"   Execution time: {response.get('execution_time_ms', 0):.2f} ms")
            else:
                print(f"\n⚠️  WARNING: Status = {response.get('status')}")
                print(f"   Error: {response.get('error', 'Unknown')}")
        else:
            print("\n❌ ERROR: No response received from CLI")

        # Cleanup
        proc.terminate()
        proc.wait(timeout=2)

        print("\n" + "=" * 60)
        print("Test complete")
        print("=" * 60)

    except subprocess.TimeoutExpired:
        print("\n❌ ERROR: Process timeout")
        proc.kill()
        return False
    except FileNotFoundError:
        print("\n❌ ERROR: dase_cli.exe not found")
        print("   Please build the CLI first:")
        print("   cd build && cmake .. && cmake --build . --config Release")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON response")
        print(f"   {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_cli_basic()
