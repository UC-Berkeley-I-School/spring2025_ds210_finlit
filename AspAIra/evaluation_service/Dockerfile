# Dockerfile.evaluator
# Use the pre-built base image from your repository (built via dockerfile.base)
FROM 010686666595.dkr.ecr.us-east-1.amazonaws.com/aspaira-backend-base:v1

# Set working directory and environment variables for the evaluator service.
# We override the working directory from /base to /app, where your full repository code will reside.
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Copy the entire repository into the container.
COPY . .

# (Optional) If your evaluator doesn't serve web traffic, you can omit EXPOSE.
# EXPOSE 8000

# Command to run the evaluator service as a module.
CMD ["python", "-m", "evaluation_service.evaluator"]