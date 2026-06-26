FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY pyrit_dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyrit_dashboard/main.py .

# In production: use gunicorn with multiple workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
