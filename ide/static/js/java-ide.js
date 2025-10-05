(async function() {
  // Initialize ACE Editor
  const editor = ace.edit("editor", {
    mode: "ace/mode/java", // Change if you want other languages
    theme: "ace/theme/monokai",
    fontSize: "14px",
    showPrintMargin: false,
    wrap: true,
  });

  editor.setValue(`import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter n: ");
        int n = scanner.nextInt();
        scanner.nextLine();
        System.out.println("Fibonacci of " + n + " is " + fib(n));
        scanner.close();
    }
    public static long fib(int n) {
        if (n <= 1) return n;
        return fib(n-1) + fib(n-2);
    }
}`, -1);

  // Get DOM elements
  const consoleOutput = document.getElementById("console-output");
  const runBtn = document.getElementById("runBtn");
  const stopBtn = document.getElementById("stopBtn");
  const saveBtn = document.getElementById("saveBtn");
  const loadBtn = document.getElementById("loadBtn");
  const filenameInput = document.getElementById("filename");

  let ws = null;
  let isRunning = false;
  let inputBox = null;

  // Get the current hostname and use it to connect to the Java server
  // For Render deployment, we need to handle both local and production environments
  const isProduction = window.location.hostname.includes('render.com');
  
  // Since both services are running on the same domain in production,
  // we just need to use the correct WebSocket protocol and port
  const WS_URL = isProduction 
    ? `wss://${window.location.hostname}/ws` // WebSocket endpoint on same domain
    : `ws://${window.location.hostname}:8080`;

  function writeConsole(text, type = "log") {
    const line = document.createElement("div");
    line.textContent = text;
    if (type === "err") line.style.color = "#ef4444";
    if (type === "success") line.style.color = "#10b981";
    if (type === "muted") line.style.color = "#94a3b8";
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
  }

  function clearConsole() {
    consoleOutput.innerHTML = "";
  }

  // Enhanced universal prompt detector (ends with :, ?, or space)
  function isInputPrompt(line) {
    return /[:?]\s*$|\s$/.test(line.trim());
  }

  function createInputBox(promptText) {
    if (inputBox) return;

    const inputLine = document.createElement("div");
    inputLine.style.display = "flex";
    inputLine.style.alignItems = "center";
    inputLine.style.gap = "8px";
    inputLine.style.marginBottom = "4px";

    const promptSpan = document.createElement("span");
    promptSpan.textContent = promptText;
    promptSpan.style.whiteSpace = "pre";
    inputLine.appendChild(promptSpan);

    inputBox = document.createElement("input");
    inputBox.type = "text";
    inputBox.placeholder = "";
    inputBox.style.minWidth = "100px";
    inputBox.style.width = "100px";
    inputBox.style.maxWidth = "700px";
    inputBox.style.background = "#1e293b";
    inputBox.style.border = "1px solid #475569";
    inputBox.style.borderRadius = "4px";
    inputBox.style.padding = "4px 8px";
    inputBox.style.color = "#f1f5f9";
    inputBox.style.fontFamily = "inherit";
    inputBox.style.fontSize = "13px";
    inputBox.style.outline = "none";
    inputBox.style.boxSizing = "content-box";

    // Dynamic, robust resizing
    const autoResize = () => {
      const temp = document.createElement("span");
      temp.style.visibility = "hidden";
      temp.style.position = "absolute";
      temp.style.whiteSpace = "pre";
      temp.style.font = window.getComputedStyle(inputBox).font;
      temp.textContent = inputBox.value || inputBox.placeholder || "";
      document.body.appendChild(temp);

      let newWidth = temp.offsetWidth + 30;
      newWidth = Math.max(100, Math.min(700, newWidth));
      inputBox.style.width = newWidth + "px";
      document.body.removeChild(temp);
    };
    inputBox.addEventListener("input", autoResize);
    inputBox.addEventListener("focus", autoResize);
    autoResize();

    inputBox.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const value = inputBox.value;
        const qaLine = document.createElement("div");
        qaLine.textContent = promptText + " " + value;
        qaLine.style.marginBottom = "0px";
        consoleOutput.appendChild(qaLine);

        inputLine.remove();

        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "input", value }));
        }

        inputBox = null;
      }
    });

    inputLine.appendChild(inputBox);
    consoleOutput.appendChild(inputLine);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    inputBox.focus();
  }

  async function runCode() {
    if (isRunning) return;

    clearConsole();
    runBtn.disabled = true;
    stopBtn.disabled = false;
    isRunning = true;

    const code = editor.getValue();

    try {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        writeConsole("Running...\n", "muted");
        ws.send(JSON.stringify({ type: 'execute', code: code }));
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'output') {
          const lines = message.data.split('\n');
          lines.forEach(line => {
            if (!line.trim()) return;
            if (isInputPrompt(line)) {
              if (!inputBox) createInputBox(line);
            } else {
              writeConsole(line);
            }
          });
        } else if (message.type === 'error') {
          writeConsole(message.data, "err");
        } else if (message.type === 'done') {
          writeConsole(
            message.success ? "\n[Program finished]" : "\n[Program finished with errors]",
            message.success ? "success" : "err"
          );
          cleanup();
        }
      };

      ws.onerror = (error) => {
        writeConsole("Connection error. Make sure the Java server is running at " + WS_URL, "err");
        writeConsole("If you're accessing from another device, ensure both devices are on the same network.", "err");
        writeConsole("Check that port 8080 is not blocked by a firewall.", "err");
        cleanup();
      };

      ws.onclose = () => {
        if (isRunning) cleanup();
      };

    } catch (error) {
      writeConsole("Error: " + error.message, "err");
      cleanup();
    }
  }

  function stopExecution() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }));
    }
    cleanup();
  }

  function cleanup() {
    isRunning = false;
    runBtn.disabled = false;
    stopBtn.disabled = true;
    if (inputBox) {
      try { inputBox.parentElement.remove(); } catch (e) {}
      inputBox = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  saveBtn.onclick = () => {
    const code = editor.getValue();
    const filename = filenameInput.value || 'Main.java';
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    clearConsole();
    writeConsole(`File saved as ${filename}`, "success");
  };

  loadBtn.onclick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.java,.txt';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          editor.setValue(event.target.result, -1);
          filenameInput.value = file.name;
          clearConsole();
          writeConsole(`Loaded ${file.name}`, "success");
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  runBtn.addEventListener("click", runCode);
  stopBtn.addEventListener("click", stopExecution);

  editor.commands.addCommand({
    name: 'runCode',
    bindKey: { win: 'Ctrl-Enter', mac: 'Command-Enter' },
    exec: runCode
  });

  editor.commands.addCommand({
    name: 'saveFile',
    bindKey: { win: 'Ctrl-S', mac: 'Command-S' },
    exec: () => saveBtn.click()
  });

  editor.session.on('change', function() {
    clearTimeout(window.autoSaveTimer);
    window.autoSaveTimer = setTimeout(() => {
      localStorage.setItem('javaCode', editor.getValue());
    }, 1000);
  });

  const savedCode = localStorage.getItem('javaCode');
  if (savedCode) {
    editor.setValue(savedCode, -1);
  }

  writeConsole("Java IDE Ready! Press ▶ Run or Ctrl+Enter to execute.", "success");
})();
