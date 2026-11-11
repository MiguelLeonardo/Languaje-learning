# syntax=docker/dockerfile:1
FROM python:3.11-slim AS build
WORKDIR /src
RUN pip install --no-cache-dir --upgrade pip
COPY backend/pyproject.toml backend/
COPY backend/app backend/app
RUN pip install --no-cache-dir --prefix=/install ./backend

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 \
    CONTENT_DIR=/srv/content/scenarios
RUN useradd --create-home --uid 10001 app
COPY --from=build /install /usr/local
WORKDIR /srv
COPY backend/app /srv/app
COPY content /srv/content
USER app
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health')"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
