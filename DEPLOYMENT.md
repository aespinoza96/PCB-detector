# PCB Detector API - Production Deployment Guide

## Overview
This guide covers deploying the PCB Detector API to production with security, monitoring, and scalability considerations.

## Pre-deployment Checklist

### 1. Security Configuration
- [ ] Configure authentication (JWT tokens, API keys)
- [ ] Set up HTTPS with valid SSL certificates
- [ ] Configure CORS origins for your domain
- [ ] Set up rate limiting
- [ ] Configure firewall rules

### 2. Environment Setup
- [ ] Set environment variables for production
- [ ] Configure logging to external service
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy for model files

### 3. Infrastructure
- [ ] Choose deployment platform (AWS, GCP, Azure, etc.)
- [ ] Set up load balancer
- [ ] Configure auto-scaling
- [ ] Set up CI/CD pipeline

## Deployment Options

### Option 1: Docker Deployment (Recommended)

```bash
# Build and run with Docker
docker build -t pcb-detector .
docker run -d -p 8000:8000 --name pcb-detector pcb-detector

# Or use docker-compose
docker-compose up -d
```

### Option 2: Direct Server Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option 3: Cloud Platform Deployment

#### AWS ECS/Fargate
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag pcb-detector:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/pcb-detector:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/pcb-detector:latest
```

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/pcb-detector
gcloud run deploy pcb-detector --image gcr.io/PROJECT-ID/pcb-detector --platform managed
```

## Production Configuration

### Environment Variables
Create a `.env` file:
```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Model Configuration
MODEL_PATH=/app/best.pt
CONFIDENCE_THRESHOLD=0.5
```

### Nginx Configuration (Optional)
Create `nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream pcb_detector {
        server pcb-detector:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req zone=api burst=20 nodelay;

        location / {
            proxy_pass http://pcb_detector;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
```

## Monitoring and Observability

### Health Checks
The API includes a health check endpoint:
```bash
curl http://localhost:8000/health
```

### Logging
Logs are automatically generated for:
- Request processing
- Errors and exceptions
- Model inference times
- File uploads

### Metrics to Monitor
- Request rate and response times
- Error rates
- Memory usage
- CPU utilization
- Model inference latency
- File upload sizes

## Security Best Practices

### 1. Authentication
Implement proper authentication:
```python
# Add to main.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Configure JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Rate Limiting
Add rate limiting middleware:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(request: Request, file: UploadFile = File(...)):
    # ... existing code
```

### 3. Input Validation
The API already includes:
- File size limits
- File type validation
- MIME type checking
- Path traversal protection

## Scaling Considerations

### Horizontal Scaling
- Use multiple workers with uvicorn
- Deploy behind a load balancer
- Consider using Redis for session storage

### Vertical Scaling
- Monitor resource usage
- Adjust memory and CPU limits
- Consider GPU acceleration for inference

### Caching
- Implement response caching for repeated requests
- Cache model predictions for identical images
- Use Redis or similar for distributed caching

## Backup and Recovery

### Model Files
- Store model files in version control
- Set up automated backups
- Test model loading in recovery scenarios

### Configuration
- Version control all configuration files
- Use environment-specific configs
- Document all configuration changes

## Troubleshooting

### Common Issues

1. **Model Loading Failures**
   - Check model file exists and is accessible
   - Verify file permissions
   - Check available memory

2. **Memory Issues**
   - Monitor memory usage
   - Implement image size limits
   - Consider image compression

3. **Performance Issues**
   - Profile inference times
   - Consider model optimization
   - Implement caching

### Debug Mode
For debugging, run with:
```bash
uvicorn main:app --reload --log-level debug
```

## API Documentation

Once deployed, access the interactive API documentation at:
- Swagger UI: `http://your-domain.com/docs`
- ReDoc: `http://your-domain.com/redoc`

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify the health endpoint
3. Test with a simple image first
4. Check system resources 