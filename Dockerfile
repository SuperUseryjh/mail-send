# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Initialize the database when the container starts
RUN python database.py

# Expose the port that Dash runs on
EXPOSE 8050

# Run the Dash application using Gunicorn
# Gunicorn is a WSGI HTTP server for UNIX, which is more robust for production than Flask's built-in server.
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "app:server"]