# Use the official slim Python image from the Docker Hub
FROM python:3.12-slim

# stream output to console
ENV PYTHONUNBUFFERED=1

# Install Poetry
RUN pip install poetry==1.8.2

# Set the working directory in the container
WORKDIR /app

# add /app/src to PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/app/src"

# Copy the application code to the container
COPY poetry.lock pyproject.toml /app/

# Install the dependencies using Poetry
RUN poetry install

COPY . /app

# Command to run the application
CMD ["poetry", "run", "python", "src/main.py"]
