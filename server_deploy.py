#!/usr/bin/env python3
"""
Fashion AI Server Deployment Script

This script helps manage the FastAPI server process, handling:
- Process management (start, stop, restart)
- Port conflict resolution
- Zombie process cleanup
- Health monitoring
- Environment setup

Usage:
    python server_deploy.py [command]

Commands:
    start       - Start the server process
    stop        - Stop the server process
    restart     - Restart the server process
    status      - Check server status
    ports       - List all ports used by the server
    clean       - Clean up zombie processes
    monitor     - Monitor server health
    setup       - Set up environment and dependencies
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import requests
import socket
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='server_deploy.log',
    filemode='a'
)

# Server configuration
DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"
UVICORN_CMD = "uvicorn app.main:app"
MAX_RETRY_COUNT = 5
HEALTH_CHECK_INTERVAL = 5  # seconds
LOG_DIR = Path("./logs")
SERVER_LOG_FILE = LOG_DIR / "server.log"
SERVER_ENV_FILE = ".env"
PID_FILE = "fashion_server.pid"
PROCESS_NAME = "uvicorn"

# Colors for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ensure_log_dir():
    """Create log directory if it doesn't exist"""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True)
        logging.info(f"Created log directory: {LOG_DIR}")


def write_pid_file(pid: int):
    """Write server PID to file"""
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))
    logging.info(f"PID {pid} written to {PID_FILE}")


def read_pid_file() -> Optional[int]:
    """Read server PID from file"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                return pid
        return None
    except Exception as e:
        logging.error(f"Error reading PID file: {str(e)}")
        return None


def remove_pid_file():
    """Remove PID file if it exists"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logging.info(f"Removed PID file: {PID_FILE}")
    except Exception as e:
        logging.error(f"Error removing PID file: {str(e)}")


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_free_port(start_port: int = DEFAULT_PORT) -> int:
    """Find a free port starting from the given port"""
    port = start_port
    while is_port_in_use(port):
        port += 1
        if port > start_port + 100:
            raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port+100}")
    return port


def get_server_processes() -> List[psutil.Process]:
    """Get all server processes"""
    server_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if process is uvicorn or python running uvicorn
            if (PROCESS_NAME in proc.info['name'].lower() or 
                (proc.info['name'] == 'python' and 
                 proc.info['cmdline'] and 
                 any(PROCESS_NAME in cmd for cmd in proc.info['cmdline']))):
                server_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return server_processes


def get_process_info(pid: int) -> Dict:
    """Get detailed information about a process"""
    try:
        proc = psutil.Process(pid)
        return {
            'pid': pid,
            'name': proc.name(),
            'status': proc.status(),
            'created': datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'memory_percent': proc.memory_percent(),
            'cpu_percent': proc.cpu_percent(interval=0.1),
            'cmd': ' '.join(proc.cmdline()),
            'is_running': proc.is_running()
        }
    except psutil.NoSuchProcess:
        return {'pid': pid, 'error': 'Process not found'}
    except Exception as e:
        return {'pid': pid, 'error': str(e)}


def get_port_from_cmdline(cmdline: List[str]) -> Optional[int]:
    """Extract port from command line arguments"""
    for i, arg in enumerate(cmdline):
        if arg == '--port' and i + 1 < len(cmdline):
            try:
                return int(cmdline[i + 1])
            except ValueError:
                pass
        elif arg.startswith('--port='):
            try:
                return int(arg.split('=')[1])
            except (ValueError, IndexError):
                pass
    # Default uvicorn port
    return DEFAULT_PORT


def kill_process(pid: int, force: bool = False) -> bool:
    """Kill a process by PID"""
    try:
        process = psutil.Process(pid)
        logging.info(f"Killing process {pid} (force={force})")
        
        if force:
            process.kill()  # SIGKILL
        else:
            process.terminate()  # SIGTERM
            
        # Wait for process to terminate
        gone, alive = psutil.wait_procs([process], timeout=5)
        
        if alive:
            # Process didn't terminate, force kill
            logging.warning(f"Process {pid} didn't terminate, force killing")
            for p in alive:
                p.kill()
            
        return True
    except psutil.NoSuchProcess:
        logging.warning(f"Process {pid} not found")
        return False
    except Exception as e:
        logging.error(f"Error killing process {pid}: {str(e)}")
        return False


def check_server_health(port: int = DEFAULT_PORT) -> Dict:
    """Check the health of the server"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            return {'status': 'healthy', 'details': response.json()}
        else:
            return {'status': 'unhealthy', 'code': response.status_code}
    except requests.exceptions.ConnectionError:
        return {'status': 'offline', 'error': 'Connection refused'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def command_start(port: Optional[int] = None, reload: bool = True, workers: int = 1):
    """Start the server process"""
    ensure_log_dir()
    
    # Check if server is already running
    server_procs = get_server_processes()
    if server_procs:
        print(f"{YELLOW}Warning: Server process(es) already running:{RESET}")
        for proc in server_procs:
            cmdline = proc.cmdline()
            proc_port = get_port_from_cmdline(cmdline)
            print(f"  PID: {proc.pid}, Port: {proc_port}, Command: {' '.join(cmdline)}")
        
        print("\nDo you want to:")
        print("1. Start a new server instance on a different port")
        print("2. Kill existing processes and start a new one")
        print("3. Cancel")
        
        try:
            choice = input("Enter choice [1-3]: ")
            if choice == '1':
                # Find a free port
                if port is None:
                    port = find_free_port()
                print(f"{BLUE}Starting new server on port {port}{RESET}")
            elif choice == '2':
                # Kill existing processes
                for proc in server_procs:
                    kill_process(proc.pid)
                time.sleep(2)  # Wait for processes to terminate
                if port is None:
                    port = DEFAULT_PORT
            else:
                print("Operation cancelled.")
                return
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return
    else:
        # No server running, use default or specified port
        if port is None:
            port = DEFAULT_PORT
            if is_port_in_use(port):
                port = find_free_port()
                print(f"{YELLOW}Port {DEFAULT_PORT} is in use. Using port {port} instead.{RESET}")
    
    # Start the server
    cmd = [UVICORN_CMD, "--host", DEFAULT_HOST, "--port", str(port)]
    
    if reload:
        cmd.append("--reload")
    
    if workers > 1:
        cmd.extend(["--workers", str(workers)])
    
    # Add log file
    cmd.extend(["--log-config", "app/logging_config.py"])
    
    cmd_str = " ".join(cmd)
    logging.info(f"Starting server with command: {cmd_str}")
    
    # Use nohup to keep the server running after the script exits
    server_log = open(SERVER_LOG_FILE, 'a')
    process = subprocess.Popen(
        f"nohup {cmd_str} > {SERVER_LOG_FILE} 2>&1 &",
        shell=True,
        stdout=server_log,
        stderr=server_log,
        preexec_fn=os.setsid
    )
    
    # Wait for server to start
    print(f"{BLUE}Starting server on port {port}...{RESET}")
    for _ in range(MAX_RETRY_COUNT):
        time.sleep(HEALTH_CHECK_INTERVAL)
        # Get the actual process (child of our subprocess)
        try:
            server_procs = get_server_processes()
            if server_procs:
                # Find process using our port
                for proc in server_procs:
                    cmd = proc.cmdline()
                    if str(port) in cmd:
                        pid = proc.pid
                        write_pid_file(pid)
                        print(f"{GREEN}Server started successfully!{RESET}")
                        print(f"  PID: {pid}")
                        print(f"  Port: {port}")
                        print(f"  URL: http://localhost:{port}")
                        print(f"  Logs: {SERVER_LOG_FILE}")
                        
                        # Check initial health
                        health = check_server_health(port)
                        if health['status'] == 'healthy':
                            print(f"{GREEN}Server health check passed{RESET}")
                        else:
                            print(f"{YELLOW}Server health check: {health['status']}{RESET}")
                        
                        return pid
        except Exception as e:
            logging.error(f"Error checking server processes: {str(e)}")
    
    print(f"{RED}Failed to confirm server startup after {MAX_RETRY_COUNT} attempts.{RESET}")
    print(f"Check logs at {SERVER_LOG_FILE} for details.")
    return None


def command_stop(force: bool = False):
    """Stop the server process"""
    # Try to get PID from file first
    pid = read_pid_file()
    
    if pid:
        print(f"{BLUE}Stopping server process (PID: {pid})...{RESET}")
        if kill_process(pid, force):
            print(f"{GREEN}Server process stopped.{RESET}")
            remove_pid_file()
            return True
    
    # If PID file doesn't exist or process not found, find all server processes
    server_procs = get_server_processes()
    
    if not server_procs:
        print(f"{YELLOW}No server processes found.{RESET}")
        remove_pid_file()  # Clean up PID file if it exists
        return False
    
    print(f"Found {len(server_procs)} server processes:")
    for i, proc in enumerate(server_procs, 1):
        cmdline = proc.cmdline()
        proc_port = get_port_from_cmdline(cmdline)
        print(f"{i}. PID: {proc.pid}, Port: {proc_port}, Command: {' '.join(cmdline)}")
    
    try:
        if len(server_procs) == 1:
            # Only one process, kill it
            proc = server_procs[0]
            print(f"{BLUE}Stopping server process (PID: {proc.pid})...{RESET}")
            if kill_process(proc.pid, force):
                print(f"{GREEN}Server process stopped.{RESET}")
                remove_pid_file()
                return True
            else:
                print(f"{RED}Failed to stop server process.{RESET}")
                return False
        else:
            # Multiple processes, ask which one to kill
            print("\nDo you want to:")
            print("1. Stop a specific process")
            print("2. Stop all processes")
            print("3. Cancel")
            
            choice = input("Enter choice [1-3]: ")
            
            if choice == '1':
                proc_num = int(input(f"Enter process number [1-{len(server_procs)}]: "))
                if 1 <= proc_num <= len(server_procs):
                    proc = server_procs[proc_num - 1]
                    print(f"{BLUE}Stopping server process (PID: {proc.pid})...{RESET}")
                    if kill_process(proc.pid, force):
                        print(f"{GREEN}Server process stopped.{RESET}")
                        if proc.pid == pid:
                            remove_pid_file()
                        return True
                    else:
                        print(f"{RED}Failed to stop server process.{RESET}")
                        return False
                else:
                    print(f"{RED}Invalid process number.{RESET}")
                    return False
            elif choice == '2':
                # Stop all processes
                success = True
                for proc in server_procs:
                    print(f"{BLUE}Stopping server process (PID: {proc.pid})...{RESET}")
                    if not kill_process(proc.pid, force):
                        print(f"{RED}Failed to stop server process (PID: {proc.pid}).{RESET}")
                        success = False
                
                if success:
                    print(f"{GREEN}All server processes stopped.{RESET}")
                    remove_pid_file()
                    return True
                else:
                    print(f"{YELLOW}Some server processes could not be stopped.{RESET}")
                    return False
            else:
                print("Operation cancelled.")
                return False
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return False


def command_restart(port: Optional[int] = None):
    """Restart the server process"""
    print(f"{BLUE}Restarting server...{RESET}")
    command_stop()
    time.sleep(2)  # Wait for processes to terminate
    return command_start(port)


def command_status():
    """Check server status"""
    # Try to get PID from file first
    pid = read_pid_file()
    
    if pid:
        try:
            proc = psutil.Process(pid)
            cmdline = proc.cmdline()
            proc_port = get_port_from_cmdline(cmdline)
            
            print(f"{BOLD}Server Status (from PID file):{RESET}")
            print(f"  PID: {pid}")
            print(f"  Port: {proc_port}")
            print(f"  Command: {' '.join(cmdline)}")
            print(f"  Status: {proc.status()}")
            print(f"  CPU: {proc.cpu_percent(interval=0.1):.1f}%")
            print(f"  Memory: {proc.memory_percent():.1f}%")
            
            # Check health
            health = check_server_health(proc_port)
            if health['status'] == 'healthy':
                print(f"  Health: {GREEN}Healthy{RESET}")
                if 'details' in health and 'version' in health['details']:
                    print(f"  Version: {health['details']['version']}")
            else:
                print(f"  Health: {RED}{health['status']}{RESET}")
            
            return
        except psutil.NoSuchProcess:
            print(f"{YELLOW}Server process (PID: {pid}) not found. PID file may be stale.{RESET}")
            remove_pid_file()
        except Exception as e:
            print(f"{RED}Error getting server status: {str(e)}{RESET}")
    
    # If PID file doesn't exist or process not found, find all server processes
    server_procs = get_server_processes()
    
    if not server_procs:
        print(f"{RED}No server processes found. Server is not running.{RESET}")
        return
    
    print(f"{BOLD}Found {len(server_procs)} server processes:{RESET}")
    for i, proc in enumerate(server_procs, 1):
        try:
            cmdline = proc.cmdline()
            proc_port = get_port_from_cmdline(cmdline)
            
            print(f"\n{BLUE}Process {i}:{RESET}")
            print(f"  PID: {proc.pid}")
            print(f"  Port: {proc_port}")
            print(f"  Command: {' '.join(cmdline)}")
            print(f"  Status: {proc.status()}")
            print(f"  CPU: {proc.cpu_percent(interval=0.1):.1f}%")
            print(f"  Memory: {proc.memory_percent():.1f}%")
            
            # Check health if we can determine the port
            if proc_port:
                health = check_server_health(proc_port)
                if health['status'] == 'healthy':
                    print(f"  Health: {GREEN}Healthy{RESET}")
                    if 'details' in health and 'version' in health['details']:
                        print(f"  Version: {health['details']['version']}")
                else:
                    print(f"  Health: {RED}{health['status']}{RESET}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"  {RED}Process information unavailable{RESET}")
        except Exception as e:
            print(f"  {RED}Error: {str(e)}{RESET}")


def command_ports():
    """List all ports used by the server"""
    server_procs = get_server_processes()
    
    if not server_procs:
        print(f"{RED}No server processes found.{RESET}")
        return
    
    print(f"{BOLD}Ports used by server processes:{RESET}")
    for proc in server_procs:
        try:
            cmdline = proc.cmdline()
            proc_port = get_port_from_cmdline(cmdline)
            
            # Check if port is actually in use
            port_active = is_port_in_use(proc_port)
            
            print(f"  PID: {proc.pid}")
            print(f"  Port: {proc_port} ({GREEN}Active{RESET} if {port_active} else {RED}Inactive{RESET})")
            print(f"  Command: {' '.join(cmdline)}")
            print()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"  {RED}Process information unavailable{RESET}")
        except Exception as e:
            print(f"  {RED}Error: {str(e)}{RESET}")


def command_clean():
    """Clean up zombie processes"""
    server_procs = get_server_processes()
    
    if not server_procs:
        print(f"{GREEN}No server processes found. Nothing to clean.{RESET}")
        return
    
    zombies = []
    for proc in server_procs:
        try:
            if proc.status() == psutil.STATUS_ZOMBIE:
                zombies.append(proc)
                print(f"Found zombie process: PID {proc.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # If we can't access the process info, it might be a zombie
            print(f"Found inaccessible process: PID {proc.pid} (potential zombie)")
            zombies.append(proc)
    
    if not zombies:
        print(f"{GREEN}No zombie processes found.{RESET}")
        return
    
    print(f"\nFound {len(zombies)} zombie processes.")
    print("Do you want to clean up all zombie processes? (y/n)")
    
    try:
        choice = input().lower()
        if choice == 'y':
            for proc in zombies:
                print(f"Killing process PID {proc.pid}...")
                try:
                    kill_process(proc.pid, force=True)
                except Exception as e:
                    print(f"Error killing process: {str(e)}")
            
            print(f"{GREEN}Zombie cleanup complete.{RESET}")
        else:
            print("Cleanup cancelled.")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def command_monitor(duration: int = 60, interval: int = 5):
    """Monitor server health for a period of time"""
    server_procs = get_server_processes()
    
    if not server_procs:
        print(f"{RED}No server processes found. Nothing to monitor.{RESET}")
        return
    
    # Get all ports that server processes are using
    ports = []
    for proc in server_procs:
        try:
            cmdline = proc.cmdline()
            proc_port = get_port_from_cmdline(cmdline)
            ports.append((proc.pid, proc_port))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if not ports:
        print(f"{RED}Could not determine ports for any server processes.{RESET}")
        return
    
    print(f"{BLUE}Monitoring server health for {duration} seconds (Ctrl+C to stop)...{RESET}")
    print(f"{'Time':<10} {'PID':<7} {'Port':<6} {'Status':<10} {'CPU %':<7} {'Mem %':<7} {'Health':<10}")
    print("-" * 70)
    
    start_time = time.time()
    end_time = start_time + duration
    
    try:
        while time.time() < end_time:
            current_time = int(time.time() - start_time)
            
            for pid, port in ports:
                try:
                    # Get process info
                    proc = psutil.Process(pid)
                    status = proc.status()
                    cpu_percent = proc.cpu_percent(interval=0)
                    mem_percent = proc.memory_percent()
                    
                    # Check health
                    health = check_server_health(port)
                    health_status = health['status']
                    
                    # Color-code the health status
                    if health_status == 'healthy':
                        health_color = f"{GREEN}{health_status}{RESET}"
                    else:
                        health_color = f"{RED}{health_status}{RESET}"
                    
                    print(f"{current_time:<10} {pid:<7} {port:<6} {status:<10} {cpu_percent:<7.1f} {mem_percent:<7.1f} {health_color}")
                except psutil.NoSuchProcess:
                    print(f"{current_time:<10} {pid:<7} {port:<6} {'DEAD':<10} {'-':<7} {'-':<7} {RED}offline{RESET}")
                except Exception as e:
                    print(f"{current_time:<10} {pid:<7} {port:<6} {'ERROR':<10} {'-':<7} {'-':<7} {RED}error{RESET}")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def command_setup():
    """Set up environment and dependencies"""
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print(f"{RED}Error: Python 3.7 or higher is required.{RESET}")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"{BLUE}Setting up environment...{RESET}")
    
    # Create directories
    ensure_log_dir()
    
    # Check for requirements.txt
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"{YELLOW}Warning: {requirements_file} not found. Cannot install dependencies.{RESET}")
    else:
        print(f"{BLUE}Installing dependencies from {requirements_file}...{RESET}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
            print(f"{GREEN}Dependencies installed successfully.{RESET}")
        except subprocess.CalledProcessError:
            print(f"{RED}Error: Failed to install dependencies.{RESET}")
            return False
    
    # Check for .env file
    if not os.path.exists(SERVER_ENV_FILE):
        print(f"{YELLOW}Warning: {SERVER_ENV_FILE} not found. Creating a template...{RESET}")
        with open(SERVER_ENV_FILE, 'w') as f:
            f.write("# Fashion AI Environment Variables\n")
            f.write("SERPAPI_API_KEY=\n")
            f.write("ANTHROPIC_API_KEY=\n")
            f.write("DEBUG=True\n")
        print(f"{GREEN}{SERVER_ENV_FILE} template created. Please fill in the required values.{RESET}")
    
    # Check if logging config exists
    logging_config_file = "app/logging_config.py"
    if not os.path.exists(logging_config_file):
        print(f"{YELLOW}Warning: {logging_config_file} not found. Creating it...{RESET}")
        os.makedirs(os.path.dirname(logging_config_file), exist_ok=True)
        with open(logging_config_file, 'w') as f:
            f.write('''"""
Logging configuration for Fashion AI
"""

import logging
from logging.config import dictConfig

LOG_LEVEL = "INFO"

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "access": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": LOG_LEVEL,
            "formatter": "default",
            "filename": "./logs/server.log",
        },
        "access_file": {
            "class": "logging.FileHandler",
            "level": LOG_LEVEL,
            "formatter": "access",
            "filename": "./logs/access.log",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": LOG_LEVEL},
        "uvicorn.access": {
            "handlers": ["console", "access_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "app": {"handlers": ["console", "file"], "level": LOG_LEVEL},
    },
}

dictConfig(logging_config)
''')
        print(f"{GREEN}Created {logging_config_file}{RESET}")
    
    print(f"{GREEN}Environment setup complete.{RESET}")
    print(f"{BLUE}You can now start the server with:{RESET}")
    print(f"  python {sys.argv[0]} start")
    return True


def print_usage():
    """Print usage information"""
    print(f"{BOLD}Fashion AI Server Deployment Script{RESET}")
    print(f"\n{BLUE}Usage:{RESET} python {sys.argv[0]} [command]")
    print("\nCommands:")
    print(f"  {BOLD}start{RESET}       - Start the server process")
    print(f"  {BOLD}stop{RESET}        - Stop the server process")
    print(f"  {BOLD}restart{RESET}     - Restart the server process")
    print(f"  {BOLD}status{RESET}      - Check server status")
    print(f"  {BOLD}ports{RESET}       - List all ports used by the server")
    print(f"  {BOLD}clean{RESET}       - Clean up zombie processes")
    print(f"  {BOLD}monitor{RESET}     - Monitor server health")
    print(f"  {BOLD}setup{RESET}       - Set up environment and dependencies")
    print(f"  {BOLD}help{RESET}        - Show this help message")


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2 or sys.argv[1] == 'help':
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        port = None
        if len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print(f"{RED}Error: Port must be a number.{RESET}")
                return
        command_start(port)
    elif command == 'stop':
        force = len(sys.argv) > 2 and sys.argv[2].lower() == 'force'
        command_stop(force)
    elif command == 'restart':
        port = None
        if len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print(f"{RED}Error: Port must be a number.{RESET}")
                return
        command_restart(port)
    elif command == 'status':
        command_status()
    elif command == 'ports':
        command_ports()
    elif command == 'clean':
        command_clean()
    elif command == 'monitor':
        duration = 60
        if len(sys.argv) > 2:
            try:
                duration = int(sys.argv[2])
            except ValueError:
                print(f"{RED}Error: Duration must be a number.{RESET}")
                return
        command_monitor(duration)
    elif command == 'setup':
        command_setup()
    else:
        print(f"{RED}Unknown command: {command}{RESET}")
        print_usage()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0) 