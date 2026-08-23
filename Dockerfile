FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --upgrade pip && pip install ".[product]"

COPY data /app/data
COPY frontend /app/frontend
COPY evals/m5_results /app/evals/m5_results
COPY run_api.py /app/run_api.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "acecqa_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
