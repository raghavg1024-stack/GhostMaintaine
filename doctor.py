"""Checks local services without downloading software or executing repository code."""
import json
import os
import sys
from runner_setup import health

if __name__=='__main__':
    result=health(os.environ.get('GHOST_MODEL','qwen3:4b-instruct'))
    print(json.dumps(result,indent=2))
    if not result['git']: print('Install Git, then reopen the launcher.')
    if not result['docker']: print('Start Docker Desktop and wait for its engine to become ready.')
    if result.get('remote_consent_required'):
        print('Remote Ollama is configured. The website will check it only after you opt in.')
    elif not result['ollama']:
        print('Ollama is optional: choose rules-only mode, or start Ollama for local AI.')
    elif not result['model_installed']:
        print('Optional model not installed: ollama pull '+result['model']+' (or choose an installed model in the website).')
    sys.exit(0 if result['git'] and result['docker'] else 1)
