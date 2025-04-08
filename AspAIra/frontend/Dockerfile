# Dockerfile (Frontend)
# Use the pre-built base image from your mutable ECR repository
FROM 010686666595.dkr.ecr.us-east-1.amazonaws.com/aspaira-frontend-base:latest

# Set the working directory and Python environment variables
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH="/app"

# Copy the entire application into the container
COPY . .

# Expose port 8501 for Streamlit
EXPOSE 8501

# Run the Streamlit app using the Home.py entrypoint
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]