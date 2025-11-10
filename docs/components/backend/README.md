# DASE Analog Excel - Backend Server

WebSocket server that bridges the DASE web interface to the high-performance CLI.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Start Server

```bash
npm start
```

You should see:
```
==============================================
  DASE Analog Excel Backend Server
==============================================
  HTTP:       http://localhost:3000
  WebSocket:  ws://localhost:8080
  CLI Path:   ../dase_cli/dase_cli.exe
==============================================
```

### 3. Open Web Interface

Navigate to: **http://localhost:3000/dase_interface.html**

## How It Works

```
┌─────────────┐         WebSocket          ┌──────────┐
│   Browser   │ ◄─────────────────────────► │  Node.js │
│  (Web UI)   │     JSON Commands/Results   │  Server  │
└─────────────┘                             └──────────┘
                                                  │
                                                  │ stdin/stdout
                                                  ▼
                                            ┌──────────┐
                                            │ DASE CLI │
                                            │  (.exe)  │
                                            └──────────┘
```

## Architecture

- **HTTP Server** (Port 3000): Serves static HTML/JS/CSS
- **WebSocket Server** (Port 8080): Real-time CLI communication
- **Process Management**: One CLI process per connected client

## API

### WebSocket Protocol

**Client → Server (Command):**
```json
{
  "command": "create_engine",
  "params": {
    "engine_type": "phase4b",
    "num_nodes": 2048
  }
}
```

**Server → Client (Response):**
```json
{
  "status": "success",
  "command": "create_engine",
  "result": {
    "engine_id": "engine_001",
    "engine_type": "phase4b",
    "num_nodes": 2048
  },
  "execution_time_ms": 0.084
}
```

## Configuration

Edit `server.js` to change:
- `PORT`: HTTP server port (default: 3000)
- `WS_PORT`: WebSocket port (default: 8080)
- CLI path (default: `../dase_cli/dase_cli.exe`)

## Development

For auto-restart on file changes:
```bash
npm run dev
```

## Troubleshooting

### "DASE CLI not found"
- Verify `dase_cli.exe` exists in `../dase_cli/`
- Check paths are correct in `server.js`

### "Port already in use"
- Change `PORT` or `WS_PORT` in `server.js`
- Or kill existing process:
  ```bash
  # Windows
  netstat -ano | findstr :3000
  taskkill /PID <PID> /F
  ```

### WebSocket connection fails
- Check firewall isn't blocking port 8080
- Ensure server is running before opening web page
- Check browser console for errors

## Testing

Test the server directly:

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8080');
ws.onopen = () => {
  ws.send(JSON.stringify({
    command: 'get_capabilities',
    params: {}
  }));
};
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Production Deployment

For production, consider:
1. **HTTPS/WSS**: Use SSL certificates
2. **Authentication**: Add token-based auth
3. **Rate Limiting**: Prevent abuse
4. **Monitoring**: Log requests and errors
5. **Process Pool**: Reuse CLI processes
6. **Docker**: Containerize for easy deployment

## License

MIT
