#!/bin/bash

# startup script for aasp_web

# collect static
python3 manage.py collectstatic --no-input

# migrate
python3 manage.py migrate --no-input

# run gunicorn
gunicorn --bind 0.0.0.0:8000 aasp.wsgi
