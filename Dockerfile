FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir flask jsonschema requests langdetect

COPY . .

EXPOSE 5000

ENV PORT=5000

CMD ["python", "run_web.py"]
