#!/bin/bash
# Test script to verify grok_local.py can list files
source venv/bin/activate
python grok_local.py --ask 'list files' --debug
deactivate
