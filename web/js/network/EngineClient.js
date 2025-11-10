/**
 * DASE Engine Client
 * Handles communication with the C++ DASE engine via WebSocket/REST API
 */

import { EngineConfig } from '../config.js';

export class EngineClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.callbacks = {
            onConnect: [],
            onDisconnect: [],
            onMessage: [],
            onError: [],
            onMetrics: [],
            onBenchmarkComplete: []
        };

        // Engine state
        this.engineHandle = null;
        this.engineVersion = EngineConfig.engine.defaultVersion;
        this.lastMetrics = null;
    }

    // ========================================================================
    // CONNECTION MANAGEMENT
    // ========================================================================

    connect() {
        const { host, port, protocol } = EngineConfig.server;
        const wsUrl = `${protocol}://${host}:${port}/ws`;

        this.log('Connecting to engine server:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            this.log('✅ Connected to DASE engine');
            this._triggerCallbacks('onConnect');
        };

        this.ws.onmessage = (event) => {
            this._handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
            this.logError('WebSocket error:', error);
            this._triggerCallbacks('onError', error);
        };

        this.ws.onclose = () => {
            this.connected = false;
            this.log('❌ Disconnected from engine');
            this._triggerCallbacks('onDisconnect');

            // Attempt reconnection
            this._attemptReconnect();
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }

    _attemptReconnect() {
        const { maxReconnectAttempts, reconnectInterval } = EngineConfig.server;

        if (this.reconnectAttempts < maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.log(`Reconnecting in ${reconnectInterval}ms (attempt ${this.reconnectAttempts}/${maxReconnectAttempts})...`);

            setTimeout(() => {
                this.connect();
            }, reconnectInterval);
        } else {
            this.logError('Max reconnection attempts reached. Please refresh the page.');
        }
    }

    // ========================================================================
    // MESSAGE HANDLING
    // ========================================================================

    _handleMessage(data) {
        try {
            const message = JSON.parse(data);
            this.log('Received:', message);

            // Trigger general message callbacks
            this._triggerCallbacks('onMessage', message);

            // Handle specific message types
            switch (message.type) {
                case 'metrics':
                    this.lastMetrics = message.data;
                    this._triggerCallbacks('onMetrics', message.data);
                    break;

                case 'benchmark_complete':
                    this._triggerCallbacks('onBenchmarkComplete', message.data);
                    break;

                case 'error':
                    this.logError('Engine error:', message.error);
                    this._triggerCallbacks('onError', message.error);
                    break;

                case 'status':
                    this.log('Engine status:', message.data);
                    break;

                default:
                    this.log('Unknown message type:', message.type);
            }
        } catch (error) {
            this.logError('Failed to parse message:', error);
        }
    }

    send(message) {
        if (!this.connected || !this.ws) {
            this.logError('Cannot send - not connected to engine');
            return false;
        }

        try {
            this.ws.send(JSON.stringify(message));
            this.log('Sent:', message);
            return true;
        } catch (error) {
            this.logError('Failed to send message:', error);
            return false;
        }
    }

    // ========================================================================
    // ENGINE COMMANDS
    // ========================================================================

    /**
     * Create a new engine instance
     * @param {number} numNodes - Number of nodes (default: 1024)
     * @param {string} version - Engine version (default: phase4b)
     */
    createEngine(numNodes = EngineConfig.engine.defaultNodes, version = null) {
        this.engineVersion = version || EngineConfig.engine.defaultVersion;

        return this.send({
            command: 'create_engine',
            params: {
                num_nodes: numNodes,
                version: this.engineVersion
            }
        });
    }

    /**
     * Destroy the engine instance
     */
    destroyEngine() {
        return this.send({
            command: 'destroy_engine'
        });
    }

    /**
     * Run a mission with the engine
     * @param {number} numSteps - Number of mission steps
     * @param {number} iterationsPerNode - Iterations per node
     */
    runMission(numSteps = EngineConfig.engine.defaultSteps, iterationsPerNode = EngineConfig.engine.iterationsPerNode) {
        return this.send({
            command: 'run_mission',
            params: {
                num_steps: numSteps,
                iterations_per_node: iterationsPerNode
            }
        });
    }

    /**
     * Run a quick benchmark
     */
    runQuickBenchmark() {
        return this.send({
            command: 'benchmark',
            params: {
                type: 'quick',
                num_nodes: EngineConfig.engine.defaultNodes,
                num_steps: EngineConfig.engine.defaultSteps,
                iterations_per_node: EngineConfig.engine.iterationsPerNode
            }
        });
    }

    /**
     * Run an endurance test
     */
    runEnduranceTest(numSteps = 5475000) {
        return this.send({
            command: 'benchmark',
            params: {
                type: 'endurance',
                num_nodes: EngineConfig.engine.defaultNodes,
                num_steps: numSteps,
                iterations_per_node: EngineConfig.engine.iterationsPerNode
            }
        });
    }

    /**
     * Get current engine metrics
     */
    getMetrics() {
        return this.send({
            command: 'get_metrics'
        });
    }

    /**
     * Get engine status
     */
    getStatus() {
        return this.send({
            command: 'status'
        });
    }

    /**
     * Set engine version
     * @param {string} version - Version name (baseline, phase3, phase4a, phase4b, phase4c)
     */
    setEngineVersion(version) {
        if (!EngineConfig.engine.versions[version]) {
            this.logError(`Unknown engine version: ${version}`);
            return false;
        }

        this.engineVersion = version;
        this.log(`Engine version set to: ${version}`);
        return true;
    }

    // ========================================================================
    // REST API METHODS (Fallback)
    // ========================================================================

    async fetchMetrics() {
        try {
            const response = await fetch(`http://${EngineConfig.server.host}:${EngineConfig.server.port}/api/metrics`);
            const data = await response.json();
            this.lastMetrics = data;
            return data;
        } catch (error) {
            this.logError('Failed to fetch metrics:', error);
            return null;
        }
    }

    async fetchStatus() {
        try {
            const response = await fetch(`http://${EngineConfig.server.host}:${EngineConfig.server.port}/api/status`);
            return await response.json();
        } catch (error) {
            this.logError('Failed to fetch status:', error);
            return null;
        }
    }

    // ========================================================================
    // CALLBACK MANAGEMENT
    // ========================================================================

    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        } else {
            this.logError(`Unknown event: ${event}`);
        }
    }

    off(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event] = this.callbacks[event].filter(cb => cb !== callback);
        }
    }

    _triggerCallbacks(event, data = null) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    this.logError(`Error in ${event} callback:`, error);
                }
            });
        }
    }

    // ========================================================================
    // UTILITY METHODS
    // ========================================================================

    getConnectionStatus() {
        return {
            connected: this.connected,
            engineVersion: this.engineVersion,
            engineHandle: this.engineHandle,
            reconnectAttempts: this.reconnectAttempts
        };
    }

    getLastMetrics() {
        return this.lastMetrics;
    }

    formatMetrics(metrics) {
        if (!metrics) return 'No metrics available';

        return `
Performance Metrics:
- Time/Op: ${metrics.ns_per_op?.toFixed(2) || 'N/A'} ns
- Throughput: ${((metrics.ops_per_sec || 0) / 1e6).toFixed(2)} M ops/sec
- Speedup: ${metrics.speedup_factor?.toFixed(2) || 'N/A'}x
- Total Ops: ${(metrics.total_operations || 0).toLocaleString()}
        `.trim();
    }

    // ========================================================================
    // LOGGING
    // ========================================================================

    log(...args) {
        if (EngineConfig.debug.enabled || EngineConfig.debug.logEngineCommands) {
            console.log('[EngineClient]', ...args);
        }
    }

    logError(...args) {
        console.error('[EngineClient]', ...args);
    }
}

export default EngineClient;
