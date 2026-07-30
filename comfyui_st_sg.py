import os
import sys
import re
import shlex
import subprocess
import time
from datetime import datetime

# --- Configuration & Paths ---

ROOT_DIR = r"..\.."  # Adjust this to point to ComfyUI root (3 levels up relative to EZi) 
                    # OR simply run from inside the project folder and use absolute paths.
    
PYTHON_EXE_ENV_PATH = "python_embeded\\python.exe" 

MAIN_PY_PATH = os.path.join(os.path.dirname(__file__), "..", "ComfyUI", "main.py")

# Default Flags based on your Batch file for headless usage
DEFAULT_ARGS = [
    "-I",                                       # -i flag: don't import site modules twice, prevents re-loading in some contexts.
    "--disable-auto-launch"                     # Ensure no browser opens automatically (headless)
]

HEADLESS_EXTRA_FLAGS = {
    "SageAttention": ["--use-sage-attention"], 
}

# Port Configuration
DEFAULT_COMFY_PORT = 8188
MAX_RETRY_COUNT     = 30      # Max retries for finding a port / handling startup check if desired

def get_python_embeded_exe():
    """Locates the python executable within the project."""
    
    candidates = [
        os.path.join(ROOT_DIR, PYTHON_EXE_ENV_PATH) if 'ROOT_DIR' in locals() else "python_embeded\\python.exe",
        sys.executable  # Fallback to current interpreter (e.g. standard Python installation)
    ]
    
    for path in reversed(candidates):
        full_path = os.path.abspath(path).replace("\\\\","\\") if "\\" in str(os.sep) else "python_embeded\python.exe"
        
        if not os.path.exists(full_path):
            continue
            
        return full_path

def parse_port_from_command_line():
    """Reads port from arguments or defaults to 8188."""
    
    # User provided override (example usage: python script.py --port 9000)
    if "--port" in sys.argv and len(sys.argv) >= 3:
        idx = sys.argv.index("--port")
        return int(sys.argv[idx+1])
        
    DEFAULT_COMFY_PORT

def is_port_in_use(port):
    """Checks a port availability."""
    
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 0.5 seconds timeout for check in headless (don't hang indefinitely if busy)
            result = s.connect_ex(('127.0.0.1', port)) == 0
    except Exception: return False
    
    return result

def collect_startup_args_from_env_or_script(bat_file=None):
    """
    Parses arguments that should be passed to the python process based on environment or script config.
    Matches logic from 'Start ComfyUI SageAttention.bat'.
    
    This function mimics parsing a bat file line (which is complex in Python) but simply uses defaults 
    unless specific overrides are added via -- flags like '--port' etc.
    """
    
    extra_args = list(DEFAULT_ARGS + HEADLESS_EXTRA_FLAGS["SageAttention"])

    # Append user provided arguments if they start with -- and aren't our internal ones (e.g. --custom-node-path)
    for idx, arg in enumerate(sys.argv[1:], 0):
        # Filter out our own management args so we don't double them up weirdly unless needed
        pass 
        
    return extra_args

def main():
    
    python_exe = get_python_embeded_exe()
    if not os.path.exists(python_exe): 
        print(f"ERROR: Could not find Python executable at {python_exe}")
        sys.exit(1)

    port_to_use = parse_port_from_command_line() or DEFAULT_COMFY_PORT
        
    # Construct final command list based on batch file logic but for a standalone script run.
    # The bat uses "main.py", so we call it directly. 
    main_py_path = os.path.abspath(MAIN_PY_PATH)

    
    if is_port_in_use(port_to_use):
        print(f"[WARNING] Port {port_to_use} appears to be in use.")
        
        try:
            # Attempt a quick cleanup if possible for headless scripts, though usually left to OS
            subprocess.run(['taskkill', '/F', '/T', '/IM', 'python.exe'], stdout=subprocess.DEVNULL) 
        except Exception as e:
            pass

    args = collect_startup_args_from_env_or_script() 
    
    # Construct the list of arguments for ComfyUI process.
    cmd_list = [
        python_exe, "-I",                     # Run in isolated mode (often safer/simpler than -u)
        main_py_path,                         # Path to main script from EZi/Bat context logic 
             *args                            # Extra user or defaults flags like --use-sage-attention
    ]

    
    print(f"Starting ComfyUI...")
    if args: f"[Headless Args] {', '.join(args)}\n" else: "" 
        
    # Start subprocess. Detaching from current python process immediately so the script ends while server runs? 
    # For 'headless' automation, we want this to block or not depending on use case (Service vs Batch).
    
    if "--daemonize" in sys.argv and len(sys.argv) > 2:
        args.append('--disable-auto-launch')
        
    try:
        proc = subprocess.Popen(
            cmd_list, 
            stdout=subprocess.PIPE,   # Capture logs to script output or pipe directly
            stderr=subprocess.STDOUT  
        )
        
        print(f"ComfyUI started with PID {proc.pid}")
            
    except Exception as e:
         [f"[START ERROR] Could not start Comfy UI.\n{e}"]

if __name__ == '__main__': 
   main()
