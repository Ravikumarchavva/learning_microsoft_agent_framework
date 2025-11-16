FROM python:3.11-slim

WORKDIR /app

# Copy the self-contained interpreter into the image
COPY code-interpreter-tool.py /app/code-interpreter-tool.py

# Make sure the script is readable/executable
RUN chmod +x /app/code-interpreter-tool.py || true

ENTRYPOINT ["python", "/app/code-interpreter-tool.py"]