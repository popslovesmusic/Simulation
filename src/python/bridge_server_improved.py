#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DASE Bridge Server - Improved Version
Flask + WebSocket bridge between the DVSL/DASE HTML UI and your
compiled AVX2 engine (dase_engine).

Improvements:
- Better error handling
- Logging support
- Configuration management
- Performance monitoring
- Multiple API endpoints
"""

from flask import Flask, send_from_directory, request, jsonify
from flask_sock import Sock
import json
import threading
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import your compiled engine module
try:
    import dase_engine as de
    ENGINE_AVAILABLE = True
    logger.info("DASE Engine loaded successfully")
except ImportError as e:
    ENGINE_AVAILABLE = False
    logger.error(f"Failed to import dase_engine: {e}")
    logger.warning("Server will run in demo mode without engine functionality")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
class Config:
    HOST = "127.0.0.1"
    PORT = 5000
    DEBUG = False
    INTERFACE_FILE = "complete_dvsl_interface.html"
    WEB_DIR = Path(__file__).parent.parent.parent / "web"
    MAX_NODES = 4096
    MAX_CYCLES = 10000
    THREAD_POOL_SIZE = 4

config = Config()

# -----------------------------------------------------------------------------
# Flask app
# -----------------------------------------------------------------------------
app = Flask(__name__, static_folder=str(config.WEB_DIR))
sock = Sock(app)

# Performance metrics storage
performance_metrics = {
    "total_requests": 0,
    "active_simulations": 0,
    "total_operations": 0,
    "start_time": datetime.now().isoformat()
}

# -----------------------------------------------------------------------------
# HTTP Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the main interface"""
    try:
        return send_from_directory(str(config.WEB_DIR), config.INTERFACE_FILE)
    except FileNotFoundError:
        return jsonify({
            "error": "Interface file not found",
            "file": config.INTERFACE_FILE,
            "directory": str(config.WEB_DIR)
        }), 404

@app.route("/<path:path>")
def serve_static(path):
    """Serve static files (css, js, images)"""
    try:
        return send_from_directory(str(config.WEB_DIR), path)
    except FileNotFoundError:
        return jsonify({"error": "File not found", "path": path}), 404

@app.route("/api/status")
def api_status():
    """Get server and engine status"""
    status = {
        "server": "running",
        "engine_available": ENGINE_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "performance": performance_metrics
    }

    if ENGINE_AVAILABLE:
        try:
            status["cpu_capabilities"] = {
                "avx2": bool(de.CPUFeatures.has_avx2()),
                "fma": bool(de.CPUFeatures.has_fma())
            }
        except Exception as e:
            status["cpu_capabilities"] = {"error": str(e)}

    return jsonify(status)

@app.route("/api/metrics")
def api_metrics():
    """Get current performance metrics"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "server_metrics": performance_metrics,
        "engine_available": ENGINE_AVAILABLE
    })

@app.route("/api/benchmark", methods=["POST"])
def api_benchmark():
    """Run a benchmark test"""
    if not ENGINE_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Engine not available"
        }), 503

    try:
        data = request.get_json() or {}
        nodes = min(int(data.get("nodes", 1024)), config.MAX_NODES)
        cycles = min(int(data.get("cycles", 1000)), config.MAX_CYCLES)

        logger.info(f"Starting benchmark: {nodes} nodes, {cycles} cycles")

        engine = de.AnalogCellularEngineAVX2(nodes)

        start_time = time.perf_counter()
        engine.run_mission(cycles)
        elapsed = time.perf_counter() - start_time

        metrics = engine.get_metrics()

        result = {
            "success": True,
            "benchmark_results": {
                "nodes": nodes,
                "cycles": cycles,
                "elapsed_seconds": elapsed,
                "cpp_metrics": {
                    "total_operations": metrics.total_operations,
                    "avx2_operations": metrics.avx2_operations,
                    "current_ns_per_op": metrics.current_ns_per_op,
                    "current_ops_per_second": metrics.current_ops_per_second,
                    "speedup_factor": metrics.speedup_factor
                }
            }
        }

        performance_metrics["total_operations"] += metrics.total_operations

        logger.info(f"Benchmark completed: {elapsed:.3f}s, {metrics.current_ns_per_op:.2f} ns/op")

        return jsonify(result)

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/validate_formula", methods=["POST"])
def api_validate_formula():
    """Validate a DVSL formula"""
    try:
        data = request.get_json() or {}
        formula = data.get("formula", "")

        # Basic validation
        if not formula.startswith("="):
            return jsonify({
                "valid": False,
                "error": "Formula must start with ="
            })

        # Additional validation could be added here
        return jsonify({
            "valid": True,
            "formula": formula,
            "parsed": {
                "type": "formula",
                "expression": formula[1:]  # Remove leading =
            }
        })

    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 500

# -----------------------------------------------------------------------------
# WebSocket endpoint: /ws
# -----------------------------------------------------------------------------
@sock.route("/ws")
def ws_handler(ws):
    """Handle WebSocket connections for real-time communication"""
    client_id = id(ws)
    logger.info(f"WebSocket client connected: {client_id}")

    try:
        # Send initial capabilities
        caps = {"avx2": False, "fma": False}
        if ENGINE_AVAILABLE:
            try:
                caps = {
                    "avx2": bool(de.CPUFeatures.has_avx2()),
                    "fma": bool(de.CPUFeatures.has_fma())
                }
            except Exception as e:
                logger.error(f"Error getting CPU caps: {e}")

        ws.send(json.dumps({
            "type": "hello",
            "client_id": client_id,
            "caps": caps,
            "server_time": datetime.now().isoformat()
        }))

        # Main message loop
        while True:
            raw = ws.receive()
            if raw is None:
                break

            try:
                msg = json.loads(raw)
                performance_metrics["total_requests"] += 1
            except json.JSONDecodeError:
                ws.send(json.dumps({
                    "type": "error",
                    "error": "invalid_json"
                }))
                continue

            cmd = msg.get("command", "").lower()
            logger.debug(f"Received command from {client_id}: {cmd}")

            # Handle commands
            if cmd == "ping":
                ws.send(json.dumps({"type": "pong"}))

            elif cmd == "status":
                ws.send(json.dumps({
                    "type": "status",
                    "engine_available": ENGINE_AVAILABLE,
                    "active_simulations": performance_metrics["active_simulations"]
                }))

            elif cmd == "run":
                if not ENGINE_AVAILABLE:
                    ws.send(json.dumps({
                        "type": "error",
                        "error": "Engine not available"
                    }))
                    continue

                # Read params with validation
                nodes = min(int(msg.get("nodes", 64)), config.MAX_NODES)
                cycles = min(int(msg.get("cycles", 1000)), config.MAX_CYCLES)

                # Run in background thread
                def run_job():
                    performance_metrics["active_simulations"] += 1
                    try:
                        engine = de.AnalogCellularEngineAVX2(nodes)
                        engine.run_mission(cycles)
                        metrics = engine.get_metrics()

                        # Build metrics dict
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

                        ws.send(json.dumps({
                            "type": "run_done",
                            "metrics": out,
                            "timestamp": datetime.now().isoformat()
                        }))

                        performance_metrics["total_operations"] += out["total_operations"] or 0

                    except Exception as e:
                        logger.error(f"Simulation error: {e}", exc_info=True)
                        ws.send(json.dumps({
                            "type": "error",
                            "error": f"{type(e).__name__}: {e}"
                        }))
                    finally:
                        performance_metrics["active_simulations"] -= 1

                threading.Thread(target=run_job, daemon=True).start()
                ws.send(json.dumps({
                    "type": "run_started",
                    "nodes": nodes,
                    "cycles": cycles
                }))

            else:
                ws.send(json.dumps({
                    "type": "error",
                    "error": f"unknown_command: {cmd}"
                }))

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
    finally:
        logger.info(f"WebSocket client disconnected: {client_id}")

# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

# -----------------------------------------------------------------------------
# Entry
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("DASE Bridge Server Starting")
    logger.info("="*60)
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")
    logger.info(f"Interface: {config.INTERFACE_FILE}")
    logger.info(f"Web Directory: {config.WEB_DIR}")
    logger.info(f"Engine Available: {ENGINE_AVAILABLE}")

    if ENGINE_AVAILABLE:
        try:
            de.CPUFeatures.printCapabilities()
        except Exception as e:
            logger.warning(f"Could not print CPU capabilities: {e}")

    logger.info("="*60)

    # Run server (threaded=True for WebSocket + HTTP)
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )
