# Production-ready & Hardened Multi-Stage Dockerfile for Process Optimisation Streamlit Application

# Stage 1: Build stage
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Upgrade OS packages & install build dependencies
RUN apt-get update && apt-get upgrade -y && apt-get dist-upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libxrender1 \
    libxext6 \
    libsm6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ["Process Optimisation/requirements.txt", "./requirements.txt"]

# Upgrade build tools and install Python dependencies into venv
RUN pip install --no-cache-dir --upgrade pip "setuptools>=75.8.2" wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Final minimal runtime stage
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Upgrade runtime base OS packages & install minimal runtime libraries (no compiler/perl toolchains)
RUN apt-get update && apt-get upgrade -y && apt-get dist-upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libxrender1 \
    libxext6 \
    libsm6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY . .

# Create unprivileged non-root user for container execution
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose default Streamlit port
EXPOSE 8501

# Healthcheck definition
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch Streamlit app with security options
CMD ["streamlit", "run", "Process Optimisation/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=true"]

