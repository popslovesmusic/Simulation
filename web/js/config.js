/**
 * DASE Engine Configuration
 * Central configuration for connecting to the C++ engine
 */

export const EngineConfig = {
    // Server connection
    server: {
        host: 'localhost',
        port: 5000,
        protocol: window.location.protocol === 'https:' ? 'wss' : 'ws',
        reconnectInterval: 3000,
        maxReconnectAttempts: 5
    },

    // Engine parameters
    engine: {
        defaultNodes: 1024,
        defaultSteps: 54750,
        iterationsPerNode: 30,

        // Available DLL versions
        versions: {
            baseline: 'dase_engine.dll',
            phase3: 'dase_engine_phase3.dll',
            phase4a: 'dase_engine_phase4a.dll',
            phase4b: 'dase_engine_phase4b.dll', // Production recommended
            phase4c: 'dase_engine_phase4c.dll'  // Experimental
        },

        // Default version
        defaultVersion: 'phase4b'
    },

    // Performance thresholds
    performance: {
        targetNsPerOp: 8000,
        warningThreshold: 10000, // Warn if slower than this
        excellentThreshold: 3000  // Excellent performance below this
    },

    // UI settings
    ui: {
        terminalMaxLines: 1000,
        gridDefaultRows: 50,
        gridDefaultCols: 26,
        autoScrollTerminal: true
    },

    // Debug settings
    debug: {
        enabled: false, // Set to true for verbose logging
        logWebSocket: false,
        logEngineCommands: true,
        logPerformance: true
    }
};

export default EngineConfig;
