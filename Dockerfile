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

# Setup directories for assets
RUN mkdir -p /app/static/{css,js}/{dist,src} /app/static/vendor/{fontawesome,lucide,htmx} /app/static/fonts

# Download and organize fonts
RUN curl -L https://fonts.gstatic.com/s/inter/v12/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7.woff2 -o /app/static/fonts/inter-latin-300-normal.woff2 && \
    cp /app/static/fonts/inter-latin-300-normal.woff2 /app/static/fonts/inter-latin-400-normal.woff2 && \
    cp /app/static/fonts/inter-latin-300-normal.woff2 /app/static/fonts/inter-latin-700-normal.woff2

# Download and organize vendor scripts
RUN curl -L https://use.fontawesome.com/releases/v6.4.0/js/all.min.js -o /app/static/vendor/fontawesome/js/all.min.js && \
    curl -L https://unpkg.com/lucide@latest/dist/umd/lucide.min.js -o /app/static/vendor/lucide/lucide.min.js && \
    curl -L https://unpkg.com/htmx.org@latest/dist/htmx.min.js -o /app/static/vendor/htmx/htmx.min.js

# Install Node.js dependencies
RUN cd theme/static_src && npm install && cd /app

# Build CSS and JS
RUN cd theme/static_src && \
    NODE_ENV=production npx tailwindcss -i ./src/input.css -o ../../static/css/dist/main.min.css --minify && \
    terser ../../static/js/src/main.js -o ../../static/js/dist/main.min.js -c -m

# Garantir que temos o CSS funcional
COPY PY_VPN_backup/theme/static/css/dist/styles.css /app/theme/static/css/dist/styles.css

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
