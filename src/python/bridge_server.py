# bridge_server.py
# Minimal Flask + WebSocket bridge between the DVSL/DASE HTML UI and your
# compiled AVX2 engine (dase_engine.cp311-win_amd64.pyd).

from flask import Flask, send_from_directory, request
from flask_sock import Sock
import json
import threading
import time

# Import your compiled engine module
import dase_engine as de

# -----------------------------------------------------------------------------
# Flask app
# -----------------------------------------------------------------------------
app = Flask(__name__, static_folder='.')
sock = Sock(app)

# Serve the interface HTML (change filename if you prefer)
INDEX_FILE = "dase_interface.html"  # you can rename to complete_dvsl_interface.html

@app.route("/")
def index():
    return send_from_directory(".", INDEX_FILE)

# Optional: serve anything else in this folder (images/css/js)
@app.route("/<path:path>")
def serve_any(path):
    return send_from_directory(".", path)

# -----------------------------------------------------------------------------
# WebSocket endpoint: /ws
# -----------------------------------------------------------------------------
# Messages are simple JSON like:
#   {"command":"run", "nodes":64, "cycles":1000}
#   {"command":"ping"}
# -----------------------------------------------------------------------------
@sock.route("/ws")
def ws_handler(ws):
    # On connect, report CPU/vector capabilities once
    try:
        caps = {
            "avx2": bool(de.cpu_has_avx2()),
            "fma": bool(de.cpu_has_fma())
        }
    except Exception:
        caps = {"avx2": None, "fma": None}
    ws.send(json.dumps({"type": "hello", "caps": caps}))

    while True:
        raw = ws.receive()
        if raw is None:
            break

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            ws.send(json.dumps({"type": "error", "error": "invalid_json"}))
            continue

        cmd = msg.get("command", "").lower()

        if cmd == "ping":
            ws.send(json.dumps({"type": "pong"}))
            continue

        if cmd == "run":
            # Read params with defaults
            nodes = int(msg.get("nodes", 64))
            cycles = int(msg.get("cycles", 1000))

            # Run the engine in a worker to avoid blocking the socket
            def run_job():
                try:
                    engine = de.AnalogCellularEngineAVX2(nodes)
                    engine.run_mission(cycles)
                    metrics = engine.get_metrics()

                    # Build a compact metrics dict using fields you bound
                    out = {
                        "total_execution_time_ns": getattr(metrics, "total_execution_time_ns", None),
                        "avx2_operation_time_ns": getattr(metrics, "avx2_operation_time_ns", None),
                        "total_operations": getattr(metrics, "total_operations", None),
                        "avx2_operations": getattr(metrics, "avx2_operations", None),
                        "node_processes": getattr(metrics, "node_processes", None),
                        "harmonic_generations": getattr(metrics, "harmonic_generations", None),
                        "current_ns_per_op": getattr(metrics, "current_ns_per_op", None),
                        "current_ops_per_second": getattr(metrics, "current_ops_per_second", None),
                        "speedup_factor": getattr(metrics, "speedup_factor", None),
                    }
                    ws.send(json.dumps({"type": "run_done", "metrics": out}))
                except Exception as e:
                    ws.send(json.dumps({"type": "error", "error": f"{type(e).__name__}: {e}"}))

            threading.Thread(target=run_job, daemon=True).start()
            ws.send(json.dumps({"type": "run_started", "nodes": nodes, "cycles": cycles}))
            continue

        # Unknown
        ws.send(json.dumps({"type": "error", "error": f"unknown_command: {cmd}"}))

# -----------------------------------------------------------------------------
# Entry
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 DASE Bridge Server running at http://127.0.0.1:5000")
    print(f"   Serving {INDEX_FILE}")
    try:
        de.cpu_print_capabilities()
    except Exception:
        pass
    # threaded=True so WebSocket + HTTP share nicely
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
