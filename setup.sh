#!/usr/bin/env bash

# Create a virtual environment and install python dependencies
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Turn on the virtual environment
source venv/bin/activate

# Install dependencies
python setup.py -q install
