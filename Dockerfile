# ==============================================================================
# STAGE 1: BUILDER
# This stage installs dependencies, builds static assets, and collects static files.
# ==============================================================================
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Install build-time system dependencies, including Node.js for Tailwind CSS
RUN apt-get update && \
    apt-get install -y nodejs npm curl --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code
COPY . .

# Install Node.js dependencies and build Tailwind CSS assets
# This assumes your package.json for tailwind is in 'theme/static_src'
RUN cd theme/static_src && npm install && cd /app
RUN cd theme/static_src && npm run build

# Collect static files
RUN python manage.py collectstatic --noinput --clear


# ==============================================================================
# STAGE 2: FINAL
# This stage creates the final, lightweight, and secure production image.
# ==============================================================================
FROM python:3.11-slim-bookworm AS final

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Create a non-root user and group for security
RUN addgroup --system django-user && adduser --system --ingroup django-user django-user

# Copy Python environment from builder stage
COPY --from=builder /usr/local/ /usr/local/

# Copy application code (including collected static files) from builder stage
COPY --from=builder /app/ /app/

# Ensure the media directory exists and has the correct permissions
RUN mkdir -p /app/media && chown -R django-user:django-user /app/media

# Set ownership for the entire app directory to the non-root user
RUN chown -R django-user:django-user /app

# Switch to the non-root user
USER django-user

# Expose the port Gunicorn will run on
EXPOSE 8000

# Command to start Gunicorn
CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "core.wsgi:application"]
