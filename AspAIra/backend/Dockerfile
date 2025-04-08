# Dockerfile
# Use the pre-built base image from ECR (ensure that this image is built for linux/amd64).
FROM 010686666595.dkr.ecr.us-east-1.amazonaws.com/aspaira-backend-base:v1

# Set the working directory and environment variables for the application
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# Copy the entire application source code into the container
COPY . .

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]