@echo off

REM if the virtual environment doesn't exist, create it
if not exist ".venv" python3 -m venv .venv

REM activate the virtual environment
.venv\Scripts\activate.bat

REM install dependencies
pip install -r requirements.txt

REM run the Twisted app
twistd -y visualizer.py -n
