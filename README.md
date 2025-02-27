# AspAIra - Financial Empowerment Platform

A mobile-first financial literacy platform designed for domestic workers in Dubai, leveraging AI to provide personalized financial education and coaching.

## 🎯 Project Overview

AspAIra aims to empower domestic workers in the UAE with:
- Personalized financial literacy education
- Interactive AI-powered financial coaching
- Simple, accessible mobile interface
- Multi-language support (English/Tagalog)

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: DynamoDB
- **AI/ML**: Dify API (upcoming)
- **Infrastructure**: AWS EC2

## 📋 Prerequisites

- Python 3.8+
- Docker Desktop
- AWS Account (for production)
- Dify API Key (upcoming)

## 🚀 Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AspAIra
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

3. **Start DynamoDB Local**
   ```bash
   cd deploy
   docker-compose up -d
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

6. **Start the frontend**
   ```bash
   cd frontend
   streamlit run Home.py
   ```

## 🌐 Environment Variables

Create a `.env` file with:

```env
# Development
DYNAMODB_ENDPOINT=http://localhost:8000
AWS_REGION=local
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy

# Production
JWT_SECRET_KEY=your-secret-key
DIFY_API_KEY=your-dify-api-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

## 🚀 AWS EC2 Deployment

1. **Launch EC2 Instance**
   - Use Ubuntu Server 20.04 LTS
   - t2.micro for testing, t2.small+ for production
   - Configure security group:
     - SSH (22)
     - HTTP (80)
     - HTTPS (443)
     - Custom TCP (8501) for Streamlit
     - Custom TCP (8000) for FastAPI

2. **Install Dependencies**
   ```bash
   # Update system
   sudo apt-get update
   sudo apt-get upgrade -y

   # Install Docker
   sudo apt-get install docker.io -y
   sudo systemctl start docker
   sudo systemctl enable docker

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   # Install Python and pip
   sudo apt-get install python3-pip -y
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd AspAIra

   # Set up environment
   cp .env.example .env
   # Edit .env with production values

   # Start services
   docker-compose -f deploy/docker-compose.yml up -d
   
   # Install dependencies
   pip3 install -r requirements.txt

   # Start backend (using systemd service)
   sudo nano /etc/systemd/system/aspaira-backend.service
   sudo systemctl start aspaira-backend
   sudo systemctl enable aspaira-backend

   # Start frontend (using systemd service)
   sudo nano /etc/systemd/system/aspaira-frontend.service
   sudo systemctl start aspaira-frontend
   sudo systemctl enable aspaira-frontend
   ```

4. **Set Up Nginx (Optional)**
   ```bash
   sudo apt-get install nginx -y
   # Configure nginx for reverse proxy
   ```

## 📊 Monitoring and Maintenance

- Use AWS CloudWatch for monitoring
- Set up log rotation
- Regular database backups
- Monitor DynamoDB capacity

## 🔒 Security Considerations

- Use strong JWT secret in production
- Enable HTTPS
- Regular security updates
- Proper AWS IAM roles
- Rate limiting
- Input validation

## 📝 License

[Your License]

## 👥 Contributing

[Contribution Guidelines] 