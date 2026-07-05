FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY config ./config
COPY src ./src
COPY tests ./tests

RUN pip install --no-cache-dir -e .
CMD ["python", "-m", "risklens.main", "run", "--profile", "financial_services", "--mock"]
