Code Interpreter Tool (Docker-only)

This repository contains a self-contained `code-interpreter-tool.py` that runs
Python code in a minimal sandbox and is configured to refuse running outside
of a Docker container by default.

Files added:
- Dockerfile - builds a small image containing the interpreter
- code-interpreter-tool.py - interpreter script (stdlib-only)

Quick usage (PowerShell on Windows):

# Build the image from the repository root
cd 'd:\github\learning_microsoft_agent_framework'
docker build -t code-interpreter:local .

# Run a quick test by passing code via the CODE environment variable
docker run --rm -e CODE="print('hello from container'); result = 42" code-interpreter:local

CLI options supported by the interpreter:
- -c / --code : pass code as a command-line string
- -f / --file : pass a path (mounted into container) to a .py file to execute
- --allow-host : allow running outside Docker (only for debugging; unsafe)

Notes:
- The interpreter enforces Docker by checking for /.dockerenv and cgroup entries.
- It uses a restricted builtin set and blocks certain modules (os, subprocess, etc.).
- The tool prints a simple BEGIN/END envelope and emits an optional JSON 'result'.
