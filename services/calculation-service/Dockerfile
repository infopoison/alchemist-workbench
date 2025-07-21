# /services/calculation-service/Dockerfile

# 1. Use an official, lightweight Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /code

# 3. Copy the dependencies file and install them first
# This leverages Docker's layer caching for faster subsequent builds
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 4. Copy the application code into the container
COPY ./app /code/app

# 5. Expose the port the app will run on inside the container
EXPOSE 8000

# 6. Define the command to run the application when the container starts
# The --host 0.0.0.0 flag is crucial to make the server accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]