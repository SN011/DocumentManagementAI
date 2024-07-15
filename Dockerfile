# Use the official Python 3.12 slim image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app


# Install build tools and system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    && apt-get clean 

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Specify the command to run the app
CMD ["python", "testing_folder/twiliotest.py"]

ENV PORT=8080
EXPOSE 8080
