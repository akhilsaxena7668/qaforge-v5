#!/bin/bash
# Activating local local environment
export PATH="$PWD/env/bin:$PATH"

echo "Environment activated."
echo "Running the application..."
python run.py
