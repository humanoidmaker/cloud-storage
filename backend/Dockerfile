# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Pillow and pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -r vaultbox && chown -R vaultbox:vaultbox /app
USER vaultbox

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["api"]
