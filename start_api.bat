@echo off
REM MOFOM AI Bridge — Python FastAPI server
REM Run this before starting the Next.js dev server

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d %~dp0
python api_server.py
