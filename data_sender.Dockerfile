# data_sender.Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# COPY data_sender/requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

COPY send_data.py .

CMD ["python", "send_data.py"]