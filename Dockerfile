# Stage 1: Build with PDM
FROM python:3.9-slim as builder

# Install and configure PDM
RUN pip install -U pip && pip install pdm && \
    pdm config python.use_venv false

WORKDIR /app
COPY pyproject.toml pdm.lock ./

# Install deps (will create __pypackages__)
RUN pdm install --prod --no-lock

# Stage 2: Runtime
FROM nginx:alpine

# Install Python
RUN apk add --no-cache python3

# Copy from builder
COPY --from=builder /app /app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/__pypackages__ /app/__pypackages__

# Copy application files (now from root)
COPY app/main.py .env ./

# Environment setup
ENV PATH=/root/.local/bin:/app/__pypackages__/3.9/bin:$PATH
ENV PYTHONPATH=/app

# Nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

# Startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000
CMD ["/start.sh"]
