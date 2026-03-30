# 1. Use a slim Python image
FROM python:3.14-slim

# 2. Set environment variables for Poetry
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1

# 3. Install system dependencies and Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# 4. Copy ONLY the dependency files first (CRITICAL for caching)
COPY pyproject.toml poetry.lock* ./

# 5. Install dependencies
# We use --no-root to avoid the naming conflict you saw earlier
RUN poetry install --no-root --only main

# 6. Now copy the rest of your application code
COPY . .

# 7. Run the bot
CMD ["python", "dinkybot.py"]