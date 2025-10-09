(async function () {
  const runBtn = document.getElementById("runBtn");
  const stopBtn = document.getElementById("stopBtn");
  const consoleOutput = document.getElementById("console-output");
  const filenameInput = document.getElementById("filename");

  const editor = ace.edit("editor", {
    mode: "ace/mode/python",
    theme: "ace/theme/monokai",
    fontSize: "14px",
    showPrintMargin: false,
    wrap: true,
  });

  editor.setValue(`# Python IDE with Input Support
print("Hello, Python IDE!")
name = input("What is your name? ")
print("Hi, " + name + "!")

age = int(input("Enter your age: "))
print("You are " + str(age) + " years old.")

print("Program completed!")`, -1);

  let pyodide = null;
  let isRunning = false;

  function writeConsole(text, type = "log") {
    const line = document.createElement("div");
    line.textContent = text;
    if (type === "err") line.style.color = "#f87171";
    if (type === "success") line.style.color = "#4ade80";
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
  }

  function clearConsole() {
    consoleOutput.innerHTML = "";
  }

  function waitForInput(prompt) {
    return new Promise((resolve) => {
      // Create a container for prompt + input on same line
      const inputLine = document.createElement("div");
      inputLine.style.display = "flex";
      inputLine.style.alignItems = "center";
      inputLine.style.gap = "8px";
      inputLine.style.marginBottom = "4px";

      if (prompt) {
        const promptSpan = document.createElement("span");
        promptSpan.textContent = prompt;
        inputLine.appendChild(promptSpan);
      }

      const inputBox = document.createElement("input");
      inputBox.type = "text";
      inputBox.className = "input-box";
      inputBox.placeholder = "Type here...";
      inputBox.style.minWidth = "100px";
      inputBox.style.width = "100px";
      inputBox.style.maxWidth = "500px";
      inputBox.style.background = "#1e293b";
      inputBox.style.border = "1px solid #475569";
      inputBox.style.borderRadius = "4px";
      inputBox.style.padding = "4px 8px";
      inputBox.style.color = "#f1f5f9";
      inputBox.style.fontFamily = "inherit";
      inputBox.style.fontSize = "13px";
      
      // Auto-resize function
      const autoResize = () => {
        // Create temporary span to measure text width
        const temp = document.createElement("span");
        temp.style.visibility = "hidden";
        temp.style.position = "absolute";
        temp.style.whiteSpace = "pre";
        temp.style.font = window.getComputedStyle(inputBox).font;
        temp.textContent = inputBox.value || inputBox.placeholder;
        document.body.appendChild(temp);
        
        const newWidth = Math.max(100, Math.min(500, temp.offsetWidth + 20));
        inputBox.style.width = newWidth + "px";
        
        document.body.removeChild(temp);
      };
      
      inputBox.addEventListener("input", autoResize);
      
      inputLine.appendChild(inputBox);
      consoleOutput.appendChild(inputLine);
      consoleOutput.scrollTop = consoleOutput.scrollHeight;
      inputBox.focus();
      autoResize(); // Initial size

      inputBox.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const value = inputBox.value;
          consoleOutput.removeChild(inputLine);
          // Show what was entered on a new line with the prompt
          const echoLine = document.createElement("div");
          echoLine.textContent = (prompt || "") + value;
          consoleOutput.appendChild(echoLine);
          resolve(value);
        }
      });
    });
  }

  writeConsole("Loading Pyodide...");
  try {
    pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.0/full/",
    });
    
    // Register JS functions
    pyodide.globals.set("__js_write__", writeConsole);
    pyodide.globals.set("__js_input__", waitForInput);

    // Setup Python environment
    await pyodide.runPythonAsync(`
import sys
import builtins

# Redirect print to JS console
def js_print(*args, sep=' ', end='\\n', **kwargs):
    text = sep.join(str(arg) for arg in args)
    __js_write__(text)

builtins.print = js_print

# Make input async and accessible
async def js_input(prompt=''):
    return await __js_input__(prompt)

builtins.input = js_input
`);

    writeConsole("Pyodide ready!", "success");
    writeConsole("Ready! Press ▶ Run or Ctrl+Enter to execute code.", "success");
  } catch (err) {
    writeConsole("Error loading Pyodide: " + err, "err");
  }

  async function runCode() {
    if (!pyodide || isRunning) return;

    clearConsole();
    runBtn.disabled = true;
    stopBtn.disabled = false;
    isRunning = true;

    const code = editor.getValue();

    try {
      // Parse the code and add await before all input() calls
      let processedCode = code;
      
      // Simple regex to add await before input( calls
      processedCode = processedCode.replace(/(\s*)input\(/g, '$1await input(');
      
      // Wrap everything in an async main function
      const wrappedCode = `
async def __main__():
${processedCode.split('\n').map(line => '    ' + line).join('\n')}

await __main__()
`;

      await pyodide.runPythonAsync(wrappedCode);
      writeConsole("\n[Program finished]", "success");
    } catch (err) {
      writeConsole("\nError: " + err.message, "err");
    } finally {
      isRunning = false;
      runBtn.disabled = false;
      stopBtn.disabled = true;
    }
  }

  function stopExecution() {
    if (isRunning) {
      writeConsole("\n[Execution stopped by user]", "err");
      isRunning = false;
      runBtn.disabled = false;
      stopBtn.disabled = true;
    }
  }

  runBtn.addEventListener("click", runCode);
  stopBtn.addEventListener("click", stopExecution);

  editor.commands.addCommand({
    name: "run",
    bindKey: { win: "Ctrl-Enter", mac: "Cmd-Enter" },
    exec: runCode,
  });
})();

(function() {
  window.addEventListener('error', function(event) {
    console.error('Global JS Error:', event.message, 'at', event.filename + ':' + event.lineno);
    const consoleOutput = document.getElementById("console-output");
    if (consoleOutput) {
      const errLine = document.createElement("div");
      errLine.textContent = `JS Error: ${event.message} at ${event.filename}:${event.lineno}`;
      errLine.style.color = "#f87171";
      consoleOutput.appendChild(errLine);
    }
  });
  window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled Promise Rejection:', event.reason);
    const consoleOutput = document.getElementById("console-output");
    if (consoleOutput) {
      const errLine = document.createElement("div");
      errLine.textContent = `Unhandled Promise Rejection: ${event.reason}`;
      errLine.style.color = "#f87171";
      consoleOutput.appendChild(errLine);
    }
  });
})();