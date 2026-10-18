@echo off
rem OpenClaw Gateway
set "TMPDIR=C:\Users\reiss\AppData\Local\Temp"
set "NODE_OPTIONS="
set "OPENCLAW_GATEWAY_PORT=18789"
set "OPENCLAW_SYSTEMD_UNIT=openclaw-gateway.service"
set "OPENCLAW_WINDOWS_TASK_NAME=OpenClaw Gateway"
set "OPENCLAW_SERVICE_MARKER=openclaw"
set "OPENCLAW_SERVICE_KIND=gateway"
C:\Users\reiss\Programme\node-v24.22.0-win-x64\node.exe --max-old-space-size=8192 C:\Users\reiss\Programme\node-v24.22.0-win-x64\node_modules\openclaw\dist\index.js gateway --port 18789 --task-supervisor < NUL
