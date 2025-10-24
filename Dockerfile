# Use the official lightweight Python image
FROM python:3.13-slim

# Ensure output is sent straight to the terminal (no buffering)
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Make start.sh executable
RUN chmod +x start.sh

# Use start.sh as entrypoint
ENTRYPOINT ["./start.sh"]

