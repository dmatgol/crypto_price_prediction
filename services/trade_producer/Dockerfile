# Use the official slim Python image from the Docker Hub
FROM python:3.12-slim

# Install curl and other necessary system dependencies
RUN apt-get update && apt-get install -y curl

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

RUN export PATH="/root/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Ensure poetry's bin directory is in PATH for all subsequent RUN instructions
ENV PATH="/root/.local/bin:$PATH"

# Install the dependencies using Poetry
RUN poetry install

# Command to run the application
CMD ["poetry", "run", "python", "src/main.py"]
