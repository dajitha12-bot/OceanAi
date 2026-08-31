# Multi-stage build for a lightweight production image
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies needed for compiling psycopg2 and scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies to a local folder
RUN pip install --no-cache-dir --user -r requirements.txt gunicorn


# Final production runner stage
FROM python:3.11-slim-bookworm as runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

# Install PostgreSQL client and GDAL/GEOS system libraries required for PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    binutils \
    libproj-dev \
    gdal-bin \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Run collectstatic at build time
RUN python manage.py collectstatic --noinput --settings=config.settings

EXPOSE 8000

# Start production server using Gunicorn - limited to 1 worker to fit in Render Free Tier 512MB RAM
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "120"]
