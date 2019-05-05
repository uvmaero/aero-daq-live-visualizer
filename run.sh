#!/bin/bash

# if the virtual environment doesn't exist, create it
if [ ! -e ".venv" ]; then
    pyvenv .venv
fi

# activate the virtual environment
source .venv/bin/activate

# install dependencies
pip3.6 install -r requirements.txt

# run the program app
python3.6 visualizer.py
