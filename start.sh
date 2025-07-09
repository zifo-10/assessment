#!/bin/sh

# Start Uvicorn (now pointing to root-level wsgi.py)
/root/.local/bin/pdm run uvicorn wsgi:app --host 0.0.0.0 --port 8001 --env-file=.env &

# Start Nginx
nginx -g "daemon off;"
