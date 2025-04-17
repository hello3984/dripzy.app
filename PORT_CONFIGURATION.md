# Fashion AI Port Configuration

This document describes the standard port configuration for the Fashion AI application.

## Standard Ports

| Service | Port | Notes |
|---------|------|-------|
| Backend | 8000 | FastAPI server running on `http://localhost:8000` |
| Frontend | 3000 | React application running on `http://localhost:3000` |

## Starting the Services

### Backend
```bash
cd backend
python run_server.py --port 8000
```

### Frontend
```bash
cd frontend
PORT=3000 npm start
```

## Troubleshooting Port Conflicts

If you encounter port conflicts, you can check for processes using these ports:

```bash
lsof -i :8000,3000
```

To kill processes using these ports:

```bash
# Find PID (process ID)
lsof -i :8000

# Kill the process
kill -9 [PID]
```

## Configuration Files

The port configuration is defined in these files:

- Frontend: `/frontend/src/services/api.js` - contains `baseURL` configuration
- Backend: Started with command line argument `--port 8000`

Do not modify these port settings without updating this document and informing all team members. 