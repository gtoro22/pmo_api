FROM python:3.11-slim

LABEL org.opencontainers.image.title="tracking-goals-invoker" \
      org.opencontainers.image.description="Invocador DDD del servicio de objetivos de Amagi"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Bogota

WORKDIR /app

# Dependencias primero para aprovechar la cache de capas
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Codigo fuente e instalacion del paquete (habilita el comando `tracking-goals`)
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

# Volumenes de trabajo
RUN mkdir -p /app/output /app/logs

# Usuario sin privilegios
RUN useradd --create-home --uid 1000 invoker \
    && chown -R invoker:invoker /app
USER invoker

ENTRYPOINT ["tracking-goals"]
CMD ["--help"]
