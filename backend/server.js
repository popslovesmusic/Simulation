/**
 * DASE Analog Excel - WebSocket Backend Server
 * Bridges the web interface to dase_cli.exe
 */

const express = require('express');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const app = express();
const PORT = 3000;
const WS_PORT = 8080;

// SECURITY CONFIGURATION (Fix C7.1, C7.2, H7.2)
const MAX_PROCESSES = 50;  // Maximum concurrent CLI processes
const MAX_BUFFER_SIZE = 10 * 1024 * 1024;  // 10MB max buffer per client
const IDLE_TIMEOUT_MS = 60 * 60 * 1000;  // 1 hour idle timeout
const COMMAND_TIMEOUT_MS = 60 * 1000;  // 1 minute command timeout

// Authentication tokens (Fix C7.2)
const validTokens = new Set([
    process.env.DASE_API_TOKEN || crypto.randomBytes(32).toString('hex')
]);

// Log valid tokens on startup (for development - remove in production)
console.log('Valid API tokens:', Array.from(validTokens));

// Track active process count (Fix C7.1)
let activeProcessCount = 0;

// Serve static files from web directory
app.use(express.static(path.join(__dirname, '../web')));

app.listen(PORT, () => {
    console.log(`HTTP server running on http://localhost:${PORT}`);
    console.log(`Open http://localhost:${PORT}/dase_interface.html in your browser`);
});

// WebSocket server for real-time CLI communication
const wss = new WebSocket.Server({ port: WS_PORT });

console.log(`WebSocket server running on ws://localhost:${WS_PORT}`);

// Track DASE CLI processes per connection
const clients = new Map();

wss.on('connection', (ws, req) => {
    // FIX C7.2: Authentication check
    const url = new URL(req.url, 'ws://localhost');
    const token = url.searchParams.get('token') || req.headers['authorization'];

    if (!validTokens.has(token)) {
        console.log('Unauthorized connection attempt');
        ws.send(JSON.stringify({
            status: 'error',
            error: 'Invalid or missing authentication token. Please provide a valid token via ?token=YOUR_TOKEN or Authorization header.',
            error_code: 'AUTH_REQUIRED'
        }));
        ws.close(1008, 'Unauthorized');
        return;
    }

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
