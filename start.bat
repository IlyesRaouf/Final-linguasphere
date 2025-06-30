@echo off
call venv\Scripts\activate.bat
set FLASK_APP=run.py
set FLASK_DEBUG=1
flask run
pause
