@echo off
cd /d "%~dp0..\backend"
set PYTHONPATH=.
set USE_MOCK_AI=true
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
