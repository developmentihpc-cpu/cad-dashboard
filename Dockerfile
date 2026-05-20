FROM python:3.12-slim

WORKDIR /app

# System libs needed by GeoPandas / pyogrio / shapely (map renderer)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY telegram_webhook.py .
COPY telegram_agent.py .
COPY country_ppt_builder.py .
COPY agent_to_builder_ctx.py .
COPY country_map_renderer.py .
COPY map_data/ ./map_data/
# Country-brief map skill (Natural Earth admin-1 polygons + flag assets).
# Required for choropleth heatmaps — without this folder the renderer
# returns None and the PPT ships placeholder rectangles.
COPY country_brief_skill/ ./country_brief_skill/

# Cloud Run injects PORT
ENV PORT=8080

# Production WSGI server
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 8 \
    --timeout 60 \
    telegram_webhook:app
