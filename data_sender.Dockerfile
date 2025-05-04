# data_sender.Dockerfile
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY datasender.txt .
RUN pip install --no-cache-dir -r datasender.txt

# Copy send_data.py directly into /app
COPY sender/send_data.py /app/sender/ 

CMD ["python", "sender/send_data.py"]