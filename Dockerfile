FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY neworder_shva.py .
COPY scheduler.py .

CMD ["python", "scheduler.py"]
