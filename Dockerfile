FROM python:3.11-slim

WORKDIR /app

COPY source-code/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY source-code/ .

EXPOSE 5000

CMD ["python", "app.py"]
