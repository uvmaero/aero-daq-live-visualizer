#!/bin/bash

# if the virtual environment doesn't exist, create it
if [ ! -e ".venv" ]; then
    python3 -m venv .venv
fi

# activate the virtual environment
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# run the Twisted app
twistd -y visualizer.py -n
