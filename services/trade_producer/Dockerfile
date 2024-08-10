# Use the official slim Python image from the Docker Hub
FROM python:3.12-slim as builder

# Install Poetry
RUN pip install poetry==1.8.2

# Determism of the build. Environment as isolated as possible
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container
WORKDIR /app

# add /app/src to PYTHONPATH
#ENV PYTHONPATH "${PYTHONPATH}:/app/src"

# Copy the application code to the container
COPY poetry.lock pyproject.toml /app/

# Provide poetry with minimal information to build the virtual
# environment to make build faster
# Remove poetry functionality of cached libraries to reduce image size
RUN poetry install --without dev  --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.12-slim as runtime

# stream output to console
ENV PYTHONUNBUFFERED=1

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app
COPY . /app

# Command to run the application
CMD [ "python", "src/main.py"]
