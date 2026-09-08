@echo off
cd /d "%~dp0.."
set VITE_API_BASE_URL=http://localhost:8000
npm.cmd --workspace frontend run dev -- --host 127.0.0.1 --port 5175
