# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt .

RUN python -m pip install \
    --prefix=/install \
    -r requirements.txt

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY --from=builder /install /usr/local

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

USER app

EXPOSE 8000

CMD ["uvicorn","app.solution:app","--host","0.0.0.0","--port","8000"]