# Use the official slim Python image from the Docker Hub
FROM python:3.12.4-slim as builder

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    musl-dev \
    libffi-dev \
    wget \
    tar \
    make \
    automake \
    build-essential \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib*

# Install Poetry
RUN pip install poetry==1.8.2

# Determism of the build. Environment as isolated as possible
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container
WORKDIR /app


# Copy the application code to the container
COPY poetry.lock pyproject.toml ./


# Provide poetry with minimal information to build the virtual
# environment to make build faster
# Remove poetry functionality of cached libraries to reduce image size
RUN poetry install --without dev  && rm -rf $POETRY_CACHE_DIR

FROM python:3.12.4-slim as runtime
COPY --from=builder /usr/lib/libta_lib.so* /usr/lib/
#stream output to console
ENV PYTHONUNBUFFERED=1

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app
COPY . .

ENV TRAIN_OR_INFERENCE = ""

EXPOSE 80

# Command to run the application
CMD if [ "$TRAIN_OR_INFERENCE" = "train" ]; then \
    python src/train.py; \
    elif [ "$TRAIN_OR_INFERENCE" = "inference" ]; then  \
    uvicorn src.api:app --host 0.0.0.0 --port 80; \
    else \
    echo "Invalid argument: $TRAIN_OR_INFERENCE" && exit 1; \
    fi
