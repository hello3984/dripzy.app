module.exports = {
  apps: [
    {
      name: 'frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      env: {
        PORT: 3006,
        NODE_ENV: 'development'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      max_restarts: 10,
      restart_delay: 3000,
      kill_timeout: 3000,
      listen_timeout: 15000,
      exec_mode: 'fork',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: '../logs/frontend.err.log',
      out_file: '../logs/frontend.out.log',
      merge_logs: true
    },
    {
      name: 'backend',
      cwd: './backend',
      script: '../.venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env: {
        NODE_ENV: 'development'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '750M',
      max_restarts: 10,
      restart_delay: 3000,
      kill_timeout: 5000,
      listen_timeout: 15000,
      exec_mode: 'fork',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: '../logs/backend.err.log',
      out_file: '../logs/backend.out.log',
      merge_logs: true
    }
  ]
}; 