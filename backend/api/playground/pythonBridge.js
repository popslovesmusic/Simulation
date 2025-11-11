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

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('error', (err) => {
      reject(err);
    });

    proc.on('close', (code) => {
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
