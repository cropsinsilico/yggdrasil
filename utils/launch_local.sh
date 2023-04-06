#!/bin/bash
set -e
source /opt/conda/etc/profile.d/conda.sh
conda activate env
gunicorn -t 150 --bind 0.0.0.0:$PORT wsgi:app
