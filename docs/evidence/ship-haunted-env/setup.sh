#!/usr/bin/env bash
set -euo pipefail
python app.py init
python app.py test
python app.py test
