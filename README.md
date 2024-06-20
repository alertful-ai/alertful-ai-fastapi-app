# fastapi-getting-started

A sample app for getting started with FastAPI on Porter Cloud.

# Steps to setup a Python virtual environment

In root dir

- `virtualenv /tmp/venv`
- `source /tmp/venv/bin/activate`

# To run devserver

- `fastapi dev server.py` (dev mode)
- `fastapi run server.py` (prod mode)

# To Kill Server

- Find the process which is using port 8000: `sudo lsof -i:8000`
- kill process: `kill -9 $pid`