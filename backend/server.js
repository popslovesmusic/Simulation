/**
 * DASE Analog Excel - WebSocket Backend Server
 * Bridges the web interface to dase_cli.exe
 */

const express = require('express');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { configureApi } = require('./api');
const { authenticateRequest } = require('./api/auth');

const app = express();
const PORT = 3000;
const WS_PORT = 8080;

// SECURITY CONFIGURATION (Fix C7.1, C7.2, H7.2)
const MAX_PROCESSES = 50;  // Maximum concurrent CLI processes
const MAX_BUFFER_SIZE = 10 * 1024 * 1024;  // 10MB max buffer per client
const IDLE_TIMEOUT_MS = 60 * 60 * 1000;  // 1 hour idle timeout
const COMMAND_TIMEOUT_MS = 60 * 1000;  // 1 minute command timeout

// Track active process count (Fix C7.1)
let activeProcessCount = 0;

// Track running simulations
const runningSimulations = new Map();

async function launchSimulation(mission) {
    if (mission.status !== 'running') {
        mission.status = 'running';
    }
    return mission;
}

function stopSimulation(missionId) {
    const mission = runningSimulations.get(missionId);
    if (mission) {
        mission.status = 'terminated';
    }
    return mission;
}

// Add JSON body parser middleware
app.use(express.json());

// Serve static files from web directory
app.use(express.static(path.join(__dirname, '../web')));

const { tokens: apiTokens } = configureApi(app, {
    runningSimulations,
    launchSimulation,
    stopSimulation
});

// Create Set for WebSocket authentication
const validTokens = new Set(apiTokens);

console.log('Valid API tokens:', apiTokens);

// ============================================================================
// REST API ENDPOINTS
// ============================================================================

// GET /api/engines - List all available engine types
app.get('/api/engines', authenticateRequest, (req, res) => {
    const engines = [
        'igsoa_gw',
        'igsoa_complex',
        'igsoa_complex_2d',
        'igsoa_complex_3d',
        'phase4b',
        'satp_higgs_1d',
        'satp_higgs_2d',
        'satp_higgs_3d'
    ];
    res.json({ engines });
});

// GET /api/engines/:name - Get detailed description of an engine
app.get('/api/engines/:name', authenticateRequest, (req, res) => {
    const engineName = req.params.name;
    const cliPath = path.join(__dirname, '../dase_cli/dase_cli.exe');

    if (!fs.existsSync(cliPath)) {
        return res.status(500).json({
            error: 'DASE CLI executable not found',
            path: cliPath
        });
    }

    // Call CLI with --describe flag
    const proc = spawn(cliPath, ['--describe', engineName]);

    let output = '';
    let errorOutput = '';

    proc.stdout.on('data', (data) => {
        output += data.toString();
    });

    proc.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    proc.on('close', (code) => {
        if (code === 0 && output) {
            try {
                const description = JSON.parse(output);
                // Extract the result from success response
                if (description.status === 'success' && description.result) {
                    res.json(description.result);
                } else {
                    res.json(description);
                }
            } catch (err) {
                res.status(500).json({
                    error: 'Failed to parse engine description',
                    details: err.message,
                    output: output
                });
            }
        } else {
            res.status(404).json({
                error: 'Engine not found or description failed',
                engine: engineName,
                stderr: errorOutput
            });
        }
    });
});


// GET /api/fs - File system browser
app.get('/api/fs', authenticateRequest, (req, res) => {
    const requestedPath = req.query.path || '/missions';
    const basePath = path.join(__dirname, '..');
    const fullPath = path.join(basePath, requestedPath);

    // Security check: prevent directory traversal
    if (!fullPath.startsWith(basePath)) {
        return res.status(403).json({
            error: 'Access denied',
            reason: 'Path traversal attempt blocked'
        });
    }

    // Check if path exists
    if (!fs.existsSync(fullPath)) {
        return res.status(404).json({
            error: 'Path not found',
            path: requestedPath
        });
    }

    // Read directory
    fs.readdir(fullPath, (err, files) => {
        if (err) {
            return res.status(500).json({
                error: 'Failed to read directory',
                details: err.message
            });
        }

        // Get file stats
        const fileList = files.map(file => {
            try {
                const stats = fs.statSync(path.join(fullPath, file));
                return {
                    name: file,
                    type: stats.isDirectory() ? 'directory' : 'file',
                    size: stats.size,
                    modified: stats.mtime.toISOString()
                };
            } catch (err) {
                return {
                    name: file,
                    type: 'unknown',
                    error: err.message
                };
            }
        });

        res.json({
            path: requestedPath,
            files: fileList
        });
    });
});

// POST /api/analysis - Run Python analysis script
app.post('/api/analysis', authenticateRequest, (req, res) => {
    const { script, target_file, args } = req.body;

    if (!script || !target_file) {
        return res.status(400).json({
            error: 'Missing required parameters',
            required: ['script', 'target_file']
        });
    }

    const scriptPath = path.join(__dirname, '../analysis', script);
    const targetPath = path.join(__dirname, '../results', target_file);

    // Security checks
    if (!fs.existsSync(scriptPath)) {
        return res.status(404).json({
            error: 'Analysis script not found',
            script: script
        });
    }

    if (!fs.existsSync(targetPath)) {
        return res.status(404).json({
            error: 'Target file not found',
            file: target_file
        });
    }

    // Build Python command
    const pythonArgs = [scriptPath, targetPath];
    if (args && typeof args === 'object') {
        for (const [key, value] of Object.entries(args)) {
            pythonArgs.push(`--${key}`);
            pythonArgs.push(value.toString());
        }
    }

    // Spawn Python process
    const proc = spawn('python', pythonArgs);

    let output = '';
    let errorOutput = '';

    proc.stdout.on('data', (data) => {
        output += data.toString();
    });

    proc.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    proc.on('close', (code) => {
        res.json({
            exit_code: code,
            stdout: output,
            stderr: errorOutput,
            success: code === 0
        });
    });

    // Timeout after 5 minutes
    setTimeout(() => {
        proc.kill('SIGTERM');
        res.status(408).json({
            error: 'Analysis timeout (5 minutes)',
            partial_output: output
        });
    }, 5 * 60 * 1000);
});

// ============================================================================
// HTTP Server Start
// ============================================================================

app.listen(PORT, () => {
    console.log(`HTTP server running on http://localhost:${PORT}`);
    console.log(`Open http://localhost:${PORT}/dase_interface.html in your browser`);
});

// WebSocket server for real-time CLI communication
const wss = new WebSocket.Server({ port: WS_PORT });

console.log(`WebSocket server running on ws://localhost:${WS_PORT}`);

// Track DASE CLI processes per connection
const clients = new Map();

// Track Grid metric clients (for LIVE() function)
const gridClients = new Set();

wss.on('connection', (ws, req) => {
    // Parse URL and check which endpoint this is
    const url = new URL(req.url, 'ws://localhost');
    const pathname = url.pathname;
    const token = url.searchParams.get('token') || req.headers['authorization'];

    // Authentication check
    if (!validTokens.has(token)) {
        console.log('Unauthorized connection attempt to', pathname);
        ws.send(JSON.stringify({
            status: 'error',
            error: 'Invalid or missing authentication token. Please provide a valid token via ?token=YOUR_TOKEN or Authorization header.',
            error_code: 'AUTH_REQUIRED'
        }));
        ws.close(1008, 'Unauthorized');
        return;
    }

    // Handle /metrics endpoint for Grid LIVE() functions
    if (pathname === '/metrics' || pathname === '/ws/metrics') {
        console.log('[WebSocket] Grid metrics client connected');
        gridClients.add(ws);

        ws.on('close', () => {
            gridClients.delete(ws);
            console.log(`[WebSocket] Grid metrics client disconnected (${gridClients.size} remaining)`);
        });

        ws.on('error', (error) => {
            console.error('[WebSocket] Grid client error:', error);
            gridClients.delete(ws);
        });

        // Send welcome message
        ws.send(JSON.stringify({
            type: 'connected',
            message: 'Grid metrics stream connected'
        }));

        return; // Don't spawn CLI process for Grid clients
    }

    // Default: Handle CLI communication (existing code below)

    // FIX C7.1: Check process limit
    if (activeProcessCount >= MAX_PROCESSES) {
        console.log(`Max processes reached (${MAX_PROCESSES}), rejecting connection`);
        ws.send(JSON.stringify({
            status: 'error',
            error: `Server at capacity. Maximum ${MAX_PROCESSES} concurrent connections allowed.`,
            error_code: 'SERVER_BUSY'
        }));
        ws.close(1013, 'Server Busy');
        return;
    }

    activeProcessCount++;
    console.log(`Authenticated client connected (${activeProcessCount}/${MAX_PROCESSES} active)`);

    // Spawn DASE CLI process for this client
    const cliPath = path.join(__dirname, '../dase_cli/dase_cli.exe');

    if (!fs.existsSync(cliPath)) {
        console.error(`DASE CLI not found at: ${cliPath}`);
        ws.send(JSON.stringify({
            status: 'error',
            error: 'DASE CLI executable not found',
            error_code: 'CLI_NOT_FOUND'
        }));
        ws.close();
        return;
    }

    const daseProcess = spawn(cliPath, [], {
        cwd: path.join(__dirname, '../dase_cli'),
        stdio: ['pipe', 'pipe', 'pipe']
    });

    console.log(`Spawned DASE CLI process (PID: ${daseProcess.pid})`);

    // FIX C7.1: Add idle timeout
    let idleTimer = setTimeout(() => {
        console.log('Killing idle process (timeout reached)');
        daseProcess.kill('SIGTERM');
        ws.close(1000, 'Idle timeout');
    }, IDLE_TIMEOUT_MS);

    // Store client info
    clients.set(ws, {
        process: daseProcess,
        buffer: '',
        pendingCommands: new Map(),
        idleTimer: idleTimer
    });

    // Handle stdout from CLI (JSON responses)
    daseProcess.stdout.on('data', (data) => {
        const client = clients.get(ws);
        if (!client) return;

        // Buffer incoming data (may be partial JSON)
        client.buffer += data.toString();

        // FIX H7.2: Check buffer size to prevent overflow
        if (client.buffer.length > MAX_BUFFER_SIZE) {
            console.error(`Buffer overflow detected (${client.buffer.length} bytes), killing process`);
            daseProcess.kill('SIGKILL');
            ws.send(JSON.stringify({
                status: 'error',
                error: `Response too large (exceeded ${MAX_BUFFER_SIZE} bytes)`,
                error_code: 'BUFFER_OVERFLOW'
            }));
            ws.close(1009, 'Message too large');
            return;
        }

        // Try to parse complete JSON objects
        const lines = client.buffer.split('\n');
        client.buffer = lines.pop() || ''; // Keep incomplete line in buffer

        lines.forEach(line => {
            line = line.trim();
            if (!line) return;

            // Check for METRIC output
            if (line.startsWith('METRIC:')) {
                const metricJson = line.substring(7); // Remove "METRIC:" prefix
                try {
                    const metric = JSON.parse(metricJson);
                    console.log('Metric received:', metric);

                    const metricMessage = JSON.stringify({
                        type: 'metrics:update',
                        data: metric
                    });

                    // Push metric to CLI client
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(metricMessage);
                    }

                    // Broadcast to all Grid clients (for LIVE() functions)
                    gridClients.forEach((gridWs) => {
                        if (gridWs.readyState === WebSocket.OPEN) {
                            gridWs.send(metricMessage);
                        }
                    });
                } catch (err) {
                    console.error('Failed to parse metric:', metricJson, err.message);
                }
                return; // Don't process as regular JSON
            }

            // Regular JSON response
            try {
                const response = JSON.parse(line);
                console.log('CLI Response:', response);

                // Send response back to web client
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify(response));
                }
            } catch (err) {
                console.error('JSON parse error:', line);
                console.error('Error:', err.message);
            }
        });
    });

    // Handle stderr from CLI (errors and debug output)
    daseProcess.stderr.on('data', (data) => {
        const errorMsg = data.toString();
        console.error('CLI Error:', errorMsg);

        // Filter out DASE engine output (🚀 emojis) which goes to stderr
        if (errorMsg.includes('🚀') || errorMsg.includes('AVX2')) {
            // This is performance output, log but don't treat as error
            console.log('CLI Output:', errorMsg);
        } else {
            // Send actual errors to client
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    status: 'error',
                    error: errorMsg,
                    error_code: 'CLI_STDERR'
                }));
            }
        }
    });

    // Handle CLI process exit
    daseProcess.on('close', (code) => {
        console.log(`CLI process exited with code ${code}`);
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                status: 'error',
                error: 'CLI process terminated',
                error_code: 'CLI_EXITED',
                exit_code: code
            }));
        }
    });

    // Handle messages from web client
    ws.on('message', (message) => {
        // FIX C7.1: Reset idle timer on activity
        const client = clients.get(ws);
        if (client && client.idleTimer) {
            clearTimeout(client.idleTimer);
            client.idleTimer = setTimeout(() => {
                console.log('Killing idle process (timeout reached)');
                daseProcess.kill('SIGTERM');
                ws.close(1000, 'Idle timeout');
            }, IDLE_TIMEOUT_MS);
        }

        try {
            const command = JSON.parse(message);
            console.log('Received command:', command);

            // Validate command structure
            if (!command.command || !command.params) {
                ws.send(JSON.stringify({
                    status: 'error',
                    error: 'Invalid command format. Expected {command, params}',
                    error_code: 'INVALID_FORMAT'
                }));
                return;
            }

            // Send command to CLI
            const jsonLine = JSON.stringify(command) + '\n';
            daseProcess.stdin.write(jsonLine);
            console.log('Sent to CLI:', jsonLine.trim());

        } catch (err) {
            console.error('Message handling error:', err);
            ws.send(JSON.stringify({
                status: 'error',
                error: err.message,
                error_code: 'MESSAGE_PROCESSING_ERROR'
            }));
        }
    });

    // Handle client disconnect
    ws.on('close', () => {
        console.log('Client disconnected');
        const client = clients.get(ws);
        if (client) {
            // Clear idle timer
            if (client.idleTimer) {
                clearTimeout(client.idleTimer);
            }
            // Terminate CLI process
            if (client.process) {
                console.log('Terminating CLI process');
                client.process.kill();
            }
        }
        clients.delete(ws);

        // FIX C7.1: Decrement active process count
        if (activeProcessCount > 0) {
            activeProcessCount--;
            console.log(`Client disconnected (${activeProcessCount}/${MAX_PROCESSES} active)`);
        }
    });

    // Send connection confirmation
    ws.send(JSON.stringify({
        status: 'connected',
        message: 'Connected to DASE CLI backend',
        pid: daseProcess.pid
    }));
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down server...');

    // Kill all CLI processes
    clients.forEach((client, ws) => {
        if (client.process) {
            client.process.kill();
        }
        ws.close();
    });

    wss.close(() => {
        console.log('WebSocket server closed');
        process.exit(0);
    });
});

console.log('\n==============================================');
console.log('  DASE Analog Excel Backend Server');
console.log('==============================================');
console.log(`  HTTP:       http://localhost:${PORT}`);
console.log(`  WebSocket:  ws://localhost:${WS_PORT}`);
console.log(`  CLI Path:   ../dase_cli/dase_cli.exe`);
console.log('==============================================\n');
