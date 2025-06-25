#!/usr/bin/env python3
"""
Fashion AI Server Control Script

This script manages the Fashion AI backend server processes, including:
- Starting/stopping/restarting the server
- Checking server status and health
- Managing process cleanup to prevent zombie processes
- Handling port conflicts
"""

import os
import sys
import subprocess
import time
import signal
import json
import logging
import platform
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configuration
SERVER_PORT = 8000
ALT_PORTS = [8010, 8015]  # Alternative ports that might be used
BACKEND_DIR = Path(__file__).parent / "backend"
START_COMMAND = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(SERVER_PORT)]
HEALTH_ENDPOINT = f"http://localhost:{SERVER_PORT}/health"
LOG_FILE = Path(__file__).parent / "server_control.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("server_control")

def get_processes_on_port(port: int) -> List[Dict[str, Any]]:
    """Get all processes running on the specified port."""
    try:
        processes = []
        # Use lsof to get process info (works on macOS and Linux)
        cmd = ["lsof", "-i", f":{port}", "-sTCP:LISTEN", "-n", "-P"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({
                            "command": parts[0],
                            "pid": int(parts[1]),
                            "user": parts[2] if len(parts) > 2 else "unknown"
                        })
        return processes
    except Exception as e:
        logger.error(f"Error checking processes on port {port}: {e}")
        return []

def get_all_server_processes() -> List[Dict[str, Any]]:
    """Get all Fashion AI server processes across all possible ports."""
    all_processes = []
    for port in [SERVER_PORT] + ALT_PORTS:
        processes = get_processes_on_port(port)
        for process in processes:
            process["port"] = port
            all_processes.append(process)
    return all_processes

def is_server_process(pid: int) -> bool:
    """Check if a process ID belongs to the Fashion AI server."""
    try:
        if not psutil.pid_exists(pid):
            return False
        
        process = psutil.Process(pid)
        cmd = " ".join(process.cmdline())
        return "uvicorn" in cmd and "app.main:app" in cmd
    except Exception:
        return False

def get_child_processes(pid: int) -> List[int]:
    """Get all child processes of the given process ID."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        return [child.pid for child in children]
    except Exception as e:
        logger.error(f"Error getting child processes of PID {pid}: {e}")
        return []

def kill_process(pid: int, force: bool = False) -> bool:
    """Kill a process by its PID."""
    try:
        if not psutil.pid_exists(pid):
            logger.warning(f"Process {pid} does not exist")
            return True
        
        # Get children first
        child_pids = get_child_processes(pid)
        
        # Kill the main process
        sig = signal.SIGKILL if force else signal.SIGTERM
        os.kill(pid, sig)
        
        # Wait for process to terminate
        start_time = time.time()
        while psutil.pid_exists(pid) and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Kill the children if they still exist
        for child_pid in child_pids:
            if psutil.pid_exists(child_pid):
                try:
                    os.kill(child_pid, sig)
                except Exception:
                    pass
        
        return not psutil.pid_exists(pid)
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

def stop_server(force: bool = False) -> bool:
    """Stop the server and all related processes."""
    processes = get_all_server_processes()
    
    if not processes:
        logger.info("No server processes found to stop")
        return True
    
    success = True
    for process in processes:
        pid = process["pid"]
        port = process.get("port", SERVER_PORT)
        logger.info(f"Stopping server process {pid} on port {port}")
        
        if kill_process(pid, force):
            logger.info(f"Successfully stopped process {pid}")
        else:
            logger.warning(f"Failed to stop process {pid}")
            success = False
    
    # Double-check
    time.sleep(1)
    remaining = get_all_server_processes()
    if remaining:
        if not force:
            logger.warning(f"Some processes still running, trying force kill: {remaining}")
            return stop_server(force=True)
        else:
            logger.error(f"Failed to stop all processes: {remaining}")
            return False
    
    return success

def start_server() -> Tuple[bool, Optional[int]]:
    """Start the server if not already running."""
    processes = get_processes_on_port(SERVER_PORT)
    
    if processes:
        logger.info(f"Server already running on port {SERVER_PORT}")
        return True, processes[0]["pid"]
    
    # Change to backend directory
    try:
        os.chdir(BACKEND_DIR)
        
        # Start server as a background process
        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(
                START_COMMAND,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setpgrp
            )
        
        logger.info(f"Started server with PID {process.pid}")
        
        # Wait for server to start (max 30 seconds)
        start_time = time.time()
        server_started = False
        
        while time.time() - start_time < 30:
            time.sleep(1)
            if check_server_health():
                server_started = True
                break
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"Server process exited early with code {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False, None
        
        if not server_started:
            logger.error("Server failed to start within timeout period")
            return False, None
        
        return True, process.pid
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False, None

def restart_server() -> Tuple[bool, Optional[int]]:
    """Restart the server."""
    logger.info("Restarting server...")
    stop_server()
    time.sleep(2)  # Give it a moment to clean up
    return start_server()

def check_server_health() -> Dict[str, Any]:
    """Check if the server is healthy."""
    try:
        import requests
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Health check failed with status code {response.status_code}")
            return {"status": "unhealthy", "error": f"Status code: {response.status_code}"}
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

def diagnose_system() -> Dict[str, Any]:
    """Diagnose system status for troubleshooting."""
    diagnosis = {
        "system": platform.system(),
        "python_version": sys.version,
        "processes": {},
        "ports": {},
        "directory_exists": os.path.isdir(BACKEND_DIR),
        "memory_usage": {}
    }
    
    # Check memory usage
    try:
        virtual_memory = psutil.virtual_memory()
        diagnosis["memory_usage"] = {
            "total": f"{virtual_memory.total / (1024 * 1024 * 1024):.2f} GB",
            "available": f"{virtual_memory.available / (1024 * 1024 * 1024):.2f} GB", 
            "percent_used": f"{virtual_memory.percent}%"
        }
    except Exception as e:
        diagnosis["memory_usage"] = {"error": str(e)}
    
    # Check all ports
    for port in [SERVER_PORT] + ALT_PORTS:
        diagnosis["ports"][port] = get_processes_on_port(port)
    
    # Check for Python processes
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmd = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                if "app.main:app" in cmd:
                    python_processes.append({
                        "pid": proc.info['pid'],
                        "command": cmd
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    diagnosis["processes"]["python"] = python_processes
    
    return diagnosis

def print_status():
    """Print the current status of the server."""
    processes = get_all_server_processes()
    
    if not processes:
        print("Server status: NOT RUNNING")
        return
    
    print("Server status: RUNNING")
    print(f"Found {len(processes)} server processes:")
    
    for process in processes:
        pid = process["pid"]
        port = process.get("port", SERVER_PORT)
        print(f"  PID: {pid}, Port: {port}, Command: {process['command']}")
    
    health = check_server_health()
    print("\nServer health:")
    for key, value in health.items():
        print(f"  {key}: {value}")

def print_usage():
    """Print usage instructions."""
    print(f"""
Fashion AI Server Control Script

Usage: python {os.path.basename(__file__)} COMMAND

Commands:
  start       Start the server on port {SERVER_PORT} if not already running
  stop        Stop all server processes
  kill        Forcefully kill all server processes
  restart     Restart the server
  status      Show server status
  diagnose    Run system diagnostics for troubleshooting
  help        Show this help message
""")

if __name__ == "__main__":
    # Ensure we have psutil
    try:
        import psutil
    except ImportError:
        print("Error: psutil package is required. Install with: pip install psutil")
        print("This package is needed to manage processes reliably.")
        sys.exit(1)
    
    # Ensure we have requests for health checks
    try:
        import requests
    except ImportError:
        print("Error: requests package is required. Install with: pip install requests")
        print("This package is needed for health checks.")
        sys.exit(1)
        
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success, pid = start_server()
        if success:
            print(f"Server started successfully on port {SERVER_PORT}" + 
                  (f" with PID {pid}" if pid else ""))
            print_status()
        else:
            print("Failed to start server. Check logs for details.")
            sys.exit(1)
            
    elif command == "stop":
        if stop_server():
            print("Server stopped successfully")
        else:
            print("Failed to stop some server processes. Try 'kill' command.")
            sys.exit(1)
            
    elif command == "kill":
        if stop_server(force=True):
            print("Server processes killed successfully")
        else:
            print("Failed to kill all server processes")
            sys.exit(1)
            
    elif command == "restart":
        success, pid = restart_server()
        if success:
            print(f"Server restarted successfully on port {SERVER_PORT}" + 
                  (f" with PID {pid}" if pid else ""))
            print_status()
        else:
            print("Failed to restart server. Check logs for details.")
            sys.exit(1)
            
    elif command == "status":
        print_status()
        
    elif command == "diagnose":
        diagnosis = diagnose_system()
        print(json.dumps(diagnosis, indent=2))
        
    elif command in ["help", "-h", "--help"]:
        print_usage()
        
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1) 