# Fashion AI Server Control Guide

## Overview
The server control script (`server_control.py`) provides robust management for the Fashion AI backend server, helping to:
- Start, stop, restart, and check the status of the server
- Prevent port conflicts and zombie processes
- Monitor server health
- Provide diagnostics for troubleshooting

## Prerequisites
- Python 3.7+
- The Fashion AI backend code
- Required Python packages:
  - `psutil` for process management
  - `requests` for health checks

## Installation
Before using the server control script, install the required dependencies:

```bash
pip install psutil requests
```

## Usage
The script supports the following commands:

### Check Server Status
```bash
python server_control.py status
```
This shows all running server processes, their PIDs, ports, and the server's health status.

### Start the Server
```bash
python server_control.py start
```
Starts the server on port 8000 if it's not already running.

### Stop the Server
```bash
python server_control.py stop
```
Gracefully stops all server processes.

### Force Kill the Server
```bash
python server_control.py kill
```
Forcefully terminates all server processes when the normal stop doesn't work.

### Restart the Server
```bash
python server_control.py restart
```
Stops and then starts the server.

### Run Diagnostics
```bash
python server_control.py diagnose
```
Provides detailed system information for troubleshooting, including:
- Running processes
- Memory usage
- Port usage
- Python environment details

## Troubleshooting

### Multiple Processes
If you see multiple server processes running:
```
python server_control.py kill
python server_control.py start
```

### Port Conflicts
If another application is using port 8000:
1. Edit the `SERVER_PORT` variable in `server_control.py`
2. Update any client applications that connect to the server

### Server Not Starting
Check the log file at `server_control.log` for detailed error messages.

### Zombie Processes
If you see "ghost" processes that won't terminate:
```
python server_control.py diagnose
```
followed by:
```
python server_control.py kill
```

## Production Use
For production environments, it's recommended to:
1. Use a process manager like Supervisor or systemd
2. Configure proper logging
3. Set up monitoring and alerts

The server control script is primarily intended for development and testing environments. 