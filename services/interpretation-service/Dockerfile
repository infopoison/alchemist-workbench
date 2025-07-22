# services/interpretation-service/Dockerfile

# Use a lightweight Python base image
FROM python:3.10-slim-buster

# Set working directory in the container
WORKDIR /code

# Copy requirements file and install dependencies first (for Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app /code/app

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]