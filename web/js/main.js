/**
 * DASE Web Interface - Main Application Entry Point
 * Initializes the engine client and UI components
 */

import { EngineClient } from './network/EngineClient.js';
import { EngineConfig } from './config.js';
import { Terminal } from './components/Terminal.js';

class DASEApp {
    constructor() {
        this.engineClient = null;
        this.terminal = null; // Will be initialized when Terminal module is created
        this.initialized = false;
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) {
            console.warn('App already initialized');
            return;
        }

        console.log('🚀 Initializing DASE Web Interface...');

        // Create engine client
        this.engineClient = new EngineClient();

        // Set up engine client event handlers
        this.setupEngineEvents();

        // Connect to engine server
        this.engineClient.connect();

        // Initialize UI components (when modules are created)
        this.initializeUI();

        this.initialized = true;
        console.log('✅ DASE App initialized');
    }

    /**
     * Set up engine client event handlers
     */
    setupEngineEvents() {
        // Connection events
        this.engineClient.on('onConnect', () => {
            this.log('Connected to engine server');
            this.updateConnectionStatus(true);

            // Request initial status
            setTimeout(() => {
                this.engineClient.getStatus();
            }, 100);
        });

        this.engineClient.on('onDisconnect', () => {
            this.log('Disconnected from engine server');
            this.updateConnectionStatus(false);
        });

        this.engineClient.on('onError', (error) => {
            this.logError('Engine error:', error);
        });

        // Metrics events
        this.engineClient.on('onMetrics', (metrics) => {
            this.log('Received metrics:', metrics);
            this.displayMetrics(metrics);
        });

        // Benchmark events
        this.engineClient.on('onBenchmarkComplete', (data) => {
            this.log('Benchmark complete:', data);
            this.displayBenchmarkResults(data);
        });

        // General message events
        this.engineClient.on('onMessage', (message) => {
            if (EngineConfig.debug.logWebSocket) {
                console.log('WebSocket message:', message);
            }
        });
    }

    /**
     * Initialize UI components
     */
    initializeUI() {
        // Initialize terminal
        this.terminal = new Terminal('terminal-output');

        // Set up basic UI event handlers
        this.setupMenuHandlers();
        this.setupKeyboardShortcuts();
    }

    /**
     * Set up menu handlers
     */
    setupMenuHandlers() {
        // File menu
        document.getElementById('menu-new')?.addEventListener('click', () => this.handleNew());
        document.getElementById('menu-save')?.addEventListener('click', () => this.handleSave());
        document.getElementById('menu-load')?.addEventListener('click', () => this.handleLoad());

        // Engine menu
        document.getElementById('menu-benchmark-quick')?.addEventListener('click', () => this.runQuickBenchmark());
        document.getElementById('menu-benchmark-endurance')?.addEventListener('click', () => this.runEnduranceTest());
        document.getElementById('menu-engine-status')?.addEventListener('click', () => this.getEngineStatus());
    }

    /**
     * Set up keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+S: Save
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.handleSave();
            }

            // Ctrl+O: Load
            if (e.ctrlKey && e.key === 'o') {
                e.preventDefault();
                this.handleLoad();
            }

            // F5: Run quick benchmark
            if (e.key === 'F5') {
                e.preventDefault();
                this.runQuickBenchmark();
            }
        });
    }

    // ========================================================================
    // ENGINE COMMANDS
    // ========================================================================

    async runQuickBenchmark() {
        this.log('Running quick benchmark...');

        if (!this.engineClient.connected) {
            this.logError('Not connected to engine server');
            return;
        }

        this.engineClient.runQuickBenchmark();
    }

    async runEnduranceTest() {
        this.log('Running endurance test (this may take several minutes)...');

        if (!this.engineClient.connected) {
            this.logError('Not connected to engine server');
            return;
        }

        this.engineClient.runEnduranceTest();
    }

    async getEngineStatus() {
        if (!this.engineClient.connected) {
            this.logError('Not connected to engine server');
            return;
        }

        this.engineClient.getStatus();
    }

    // ========================================================================
    // FILE OPERATIONS
    // ========================================================================

    handleNew() {
        if (confirm('Create new workspace? Unsaved changes will be lost.')) {
            this.log('Creating new workspace...');
            // TODO: Clear grid and reset state
        }
    }

    handleSave() {
        this.log('Saving workspace...');
        // TODO: Implement save functionality
        alert('Save functionality coming soon!');
    }

    handleLoad() {
        this.log('Loading workspace...');
        // TODO: Implement load functionality
        alert('Load functionality coming soon!');
    }

    // ========================================================================
    // UI UPDATES
    // ========================================================================

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
            statusEl.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }

    displayMetrics(metrics) {
        // Display in terminal using specialized method
        if (this.terminal) {
            this.terminal.displayMetrics(metrics);
        }

        // Update UI if metrics display exists
        const metricsEl = document.getElementById('metrics-display');
        if (metricsEl) {
            const formatted = this.engineClient.formatMetrics(metrics);
            metricsEl.textContent = formatted;
        }
    }

    displayBenchmarkResults(data) {
        // Display in terminal using specialized method
        if (this.terminal) {
            this.terminal.displayBenchmarkResults(data);
        }
    }

    // ========================================================================
    // LOGGING
    // ========================================================================

    log(...args) {
        console.log('[DASEApp]', ...args);

        // Output to terminal if available
        if (this.terminal) {
            this.terminal.info(args.join(' '));
        }
    }

    logError(...args) {
        console.error('[DASEApp]', ...args);

        // Output to terminal if available
        if (this.terminal) {
            this.terminal.error(args.join(' '));
        }
    }
}

// Create global app instance
window.DASEApp = new DASEApp();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.DASEApp.init();
    });
} else {
    window.DASEApp.init();
}

// Export for module usage
export default DASEApp;
