# 1. Start with an official, lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy and install the Python libraries 
COPY ./services/lexicon-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy our service's code and the knowledge base into the container
COPY ./services/lexicon-service/ .
COPY ./knowledge_base ./knowledge_base

# 5. Define the command to run when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]