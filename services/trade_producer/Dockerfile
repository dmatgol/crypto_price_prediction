# Use the official slim Python image from the Docker Hub
FROM python:3.12-slim

# stream output to console
ENV PYTHONUNBUFFERED=1

# Install curl and other necessary system dependencies
#RUN apt-get update && apt-get install -y curl

# Install Poetry
RUN pip install poetry==1.8.2

RUN export PATH="/root/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the application code to the container
COPY poetry.lock pyproject.toml /app/

# Ensure poetry's bin directory is in PATH for all subsequent RUN instructions
ENV PATH="/root/.local/bin:$PATH"

# Install the dependencies using Poetry
RUN poetry install

COPY . /app

# Command to run the application
CMD ["poetry", "run", "python", "src/main.py"]
