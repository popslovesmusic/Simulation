const { spawn } = require('child_process');
const path = require('path');

const PYTHON_CANDIDATES = [process.env.PLAYGROUND_PYTHON, 'python3', 'python'];

function resolvePython() {
  for (const candidate of PYTHON_CANDIDATES) {
    if (!candidate) continue;
    return candidate;
  }
  return 'python3';
}

function runPythonTool(scriptRelativePath, args = [], payload = undefined) {
  return new Promise((resolve, reject) => {
    const pythonExecutable = resolvePython();
    const scriptPath = path.join(__dirname, '..', '..', 'services', scriptRelativePath);
    const proc = spawn(pythonExecutable, [scriptPath, ...args]);

    let stdout = '';
    let stderr = '';
    const MAX_OUTPUT = 1024 * 1024; // 1MB output limit
    const TIMEOUT_MS = 30000; // 30 second timeout

    // Add timeout protection
    const timeout = setTimeout(() => {
      proc.kill('SIGTERM');
      reject(new Error('Python script timeout after 30 seconds'));
    }, TIMEOUT_MS);

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
      // Enforce output size limit
      if (stdout.length > MAX_OUTPUT) {
        clearTimeout(timeout);
        proc.kill('SIGTERM');
        reject(new Error('Output size exceeded 1MB limit'));
      }
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
      // Enforce stderr limit too
      if (stderr.length > MAX_OUTPUT) {
        clearTimeout(timeout);
        proc.kill('SIGTERM');
        reject(new Error('Error output size exceeded 1MB limit'));
      }
    });

    proc.on('error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });

    proc.on('close', (code) => {
      clearTimeout(timeout); // Critical: clear timeout to prevent memory leak

      if (code !== 0 && !stdout) {
        reject(new Error(stderr || `Python script exited with code ${code}`));
        return;
      }

      try {
        const parsed = stdout ? JSON.parse(stdout) : {};
        resolve(parsed);
      } catch (error) {
        reject(new Error(`Failed to parse python output: ${error.message}. Raw output: ${stdout}`));
      }
    });

    if (payload !== undefined) {
      proc.stdin.write(JSON.stringify(payload));
    }
    proc.stdin.end();
  });
}

module.exports = {
  runPythonTool,
};
