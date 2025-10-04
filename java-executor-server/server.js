const express = require('express');
const { WebSocketServer } = require('ws');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Java Executor Server Running' });
});

const PORT = process.env.PORT || 8080;
const server = app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});

// WebSocket server
const wss = new WebSocketServer({ server });

// Temp directory for Java files
const TEMP_DIR = path.join(__dirname, 'temp');
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR);
}

// Clean up old files on startup
function cleanTempDir() {
  const files = fs.readdirSync(TEMP_DIR);
  files.forEach(file => {
    const filePath = path.join(TEMP_DIR, file);
    try {
      fs.unlinkSync(filePath);
    } catch (err) {
      console.error(`Error deleting ${file}:`, err);
    }
  });
}
cleanTempDir();

wss.on('connection', (ws) => {
  console.log('Client connected');
  
  let javaProcess = null;
  let sessionId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  
  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);
      
      if (data.type === 'execute') {
        executeJava(ws, data.code, sessionId);
      } else if (data.type === 'input') {
        if (javaProcess && javaProcess.stdin) {
          javaProcess.stdin.write(data.value + '\n');
        }
      } else if (data.type === 'stop') {
        if (javaProcess) {
          javaProcess.kill('SIGTERM');
          ws.send(JSON.stringify({ 
            type: 'output', 
            data: '\n[Execution stopped by user]\n' 
          }));
          ws.send(JSON.stringify({ type: 'done', success: false }));
        }
      }
    } catch (err) {
      ws.send(JSON.stringify({ 
        type: 'error', 
        data: 'Invalid message format: ' + err.message 
      }));
    }
  });

  async function executeJava(ws, code, sessionId) {
    const className = extractClassName(code) || 'Main';
    const javaFile = path.join(TEMP_DIR, `${className}.java`);
    const classFile = path.join(TEMP_DIR, `${className}.class`);

    try {
      // Clean up any existing files with same class name
      if (fs.existsSync(javaFile)) fs.unlinkSync(javaFile);
      if (fs.existsSync(classFile)) fs.unlinkSync(classFile);

      // Write Java file
      fs.writeFileSync(javaFile, code);

      // Compile
      ws.send(JSON.stringify({ type: 'output', data: 'Compiling...\n' }));
      
      const compileProcess = spawn('javac', [javaFile]);
      
      let compileError = '';
      compileProcess.stderr.on('data', (data) => {
        compileError += data.toString();
      });

      compileProcess.on('close', (code) => {
        if (code !== 0) {
          ws.send(JSON.stringify({ 
            type: 'error', 
            data: 'Compilation Error:\n' + compileError 
          }));
          ws.send(JSON.stringify({ type: 'done', success: false }));
          cleanup();
          return;
        }

        // Run Java program
        ws.send(JSON.stringify({ type: 'output', data: '\n' }));
        
        javaProcess = spawn('java', ['-cp', TEMP_DIR, className]);

        // Send stdout to client
        javaProcess.stdout.on('data', (data) => {
          ws.send(JSON.stringify({ 
            type: 'output', 
            data: data.toString() 
          }));
        });

        // Send stderr to client
        javaProcess.stderr.on('data', (data) => {
          ws.send(JSON.stringify({ 
            type: 'error', 
            data: data.toString() 
          }));
        });

        // Handle process exit
        javaProcess.on('close', (exitCode) => {
          ws.send(JSON.stringify({ 
            type: 'done', 
            success: exitCode === 0 
          }));
          cleanup();
          javaProcess = null;
        });

        // Handle process errors
        javaProcess.on('error', (err) => {
          ws.send(JSON.stringify({ 
            type: 'error', 
            data: 'Execution Error: ' + err.message 
          }));
          ws.send(JSON.stringify({ type: 'done', success: false }));
          cleanup();
        });

        // Timeout after 30 seconds
        setTimeout(() => {
          if (javaProcess) {
            javaProcess.kill('SIGTERM');
            ws.send(JSON.stringify({ 
              type: 'error', 
              data: '\n[Execution timeout - 30 seconds exceeded]\n' 
            }));
            ws.send(JSON.stringify({ type: 'done', success: false }));
          }
        }, 30000);
      });

    } catch (err) {
      ws.send(JSON.stringify({ 
        type: 'error', 
        data: 'Server Error: ' + err.message 
      }));
      ws.send(JSON.stringify({ type: 'done', success: false }));
      cleanup();
    }

    function cleanup() {
      try {
        if (fs.existsSync(javaFile)) fs.unlinkSync(javaFile);
        if (fs.existsSync(classFile)) fs.unlinkSync(classFile);
        
        // Clean up any additional class files (for inner classes)
        const files = fs.readdirSync(TEMP_DIR);
        files.forEach(file => {
          if (file.startsWith(className) && (file.endsWith('.class') || file.endsWith('.java'))) {
            const filePath = path.join(TEMP_DIR, file);
            try {
              fs.unlinkSync(filePath);
            } catch (e) {}
          }
        });
      } catch (err) {
        console.error('Cleanup error:', err);
      }
    }
  }

  ws.on('close', () => {
    console.log('Client disconnected');
    if (javaProcess) {
      javaProcess.kill('SIGTERM');
    }
  });

  ws.on('error', (err) => {
    console.error('WebSocket error:', err);
  });
});

// Extract class name from Java code
function extractClassName(code) {
  // Try to find public class first
  let match = code.match(/public\s+class\s+(\w+)/);
  if (match) return match[1];
  
  // If no public class, find any class
  match = code.match(/class\s+(\w+)/);
  if (match) return match[1];
  
  return null;
}

console.log('✅ WebSocket server ready on ws://localhost:' + PORT);