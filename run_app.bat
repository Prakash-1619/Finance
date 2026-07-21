@echo off
cd /d "%~dp0"
python -m streamlit run main.py --server.port 8502 --server.headless true
pause
