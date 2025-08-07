module.exports = {
  apps: [{
    name: 'mex-trading-bot',
    script: 'main.py',
    interpreter: 'python3',
    cwd: '/home/user1/MEXCAITRADE',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PYTHONPATH: '/home/user1/MEXCAITRADE'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
}; 