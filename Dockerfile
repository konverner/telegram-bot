# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the pyproject.toml and other necessary files
COPY pyproject.toml .
COPY src ./src
COPY tests ./tests

# Copy the .env file into the container
COPY .env /app/

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install optional dependencies if needed
RUN pip install --no-cache-dir ".[all]"

# Copy the rest of the application code into the container
COPY . /app

# Run the application when the container launches
CMD ["python", "-m", "src.app.main"]
