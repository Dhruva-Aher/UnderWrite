FROM python:3.13-slim

# Avoid writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure python output is unbuffered so GitHub Actions captures it in real-time
ENV PYTHONUNBUFFERED 1

# Install runtime dependencies
RUN pip install --no-cache-dir httpx==0.27.0

# Copy the deployment gate script
COPY scripts/deployment_gate.py /deployment_gate.py

# Map arguments from action.yml to the Python script
ENTRYPOINT ["python", "/deployment_gate.py"]
