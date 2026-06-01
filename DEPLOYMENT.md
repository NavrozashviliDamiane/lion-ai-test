# Lion Trans Chat AI - Deployment Guide

## Deployment Options

### Option 1: Local Development

**Best for:** Testing, development, learning

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
redis-server

# 3. Run application
python main.py

# 4. Access at http://localhost:8000
```

### Option 2: Docker Deployment

**Best for:** Production, consistency across environments

#### Build Docker Image

```bash
docker build -t lion-trans-chat-ai:latest .
```

#### Run with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  chat-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      DB_HOST: ${DB_HOST}
      DB_PORT: ${DB_PORT}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      DB_NAME: ${DB_NAME}
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - .:/app
    command: python main.py

volumes:
  redis_data:
```

#### Run Docker Compose

```bash
# Create .env file with your credentials
cat > .env << EOF
OPENAI_API_KEY=sk-...
DB_HOST=185.49.165.116
DB_PORT=3310
DB_USER=liontest_user
DB_PASSWORD=nR2aJ6eS2u
DB_NAME=vps_liontest_db
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f chat-api

# Stop services
docker-compose down
```

### Option 3: Cloud Deployment

#### AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3-pip redis-server

# 4. Clone repository
git clone <your-repo-url>
cd lion-python

# 5. Install Python packages
pip3 install -r requirements.txt

# 6. Create .env file
nano .env
# Add your credentials

# 7. Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 8. Run application with Gunicorn
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# 9. (Optional) Set up Nginx reverse proxy
sudo apt install nginx
# Configure nginx to proxy to localhost:8000
```

#### Heroku

```bash
# 1. Install Heroku CLI
# 2. Login
heroku login

# 3. Create app
heroku create lion-trans-chat-ai

# 4. Add Redis addon
heroku addons:create heroku-redis:premium-0

# 5. Set environment variables
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set DB_HOST=185.49.165.116
heroku config:set DB_PORT=3310
heroku config:set DB_USER=liontest_user
heroku config:set DB_PASSWORD=nR2aJ6eS2u
heroku config:set DB_NAME=vps_liontest_db

# 6. Deploy
git push heroku main

# 7. View logs
heroku logs --tail
```

#### Google Cloud Run

```bash
# 1. Create Dockerfile (already exists)

# 2. Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/lion-trans-chat-ai

# 3. Deploy to Cloud Run
gcloud run deploy lion-trans-chat-ai \
  --image gcr.io/PROJECT_ID/lion-trans-chat-ai \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=sk-... \
  --set-env-vars DB_HOST=185.49.165.116 \
  --set-env-vars DB_PORT=3310 \
  --set-env-vars DB_USER=liontest_user \
  --set-env-vars DB_PASSWORD=nR2aJ6eS2u \
  --set-env-vars DB_NAME=vps_liontest_db \
  --memory 2Gi \
  --timeout 3600

# 4. Get service URL
gcloud run services describe lion-trans-chat-ai --region us-central1
```

## Production Checklist

### Before Deployment

- [ ] All environment variables set in `.env`
- [ ] Database credentials verified
- [ ] OpenAI API key valid and has sufficient quota
- [ ] Redis server accessible
- [ ] All dependencies in `requirements.txt`
- [ ] Tests pass: `python test_chat_ai.py`
- [ ] Health check passes: `curl http://localhost:8000/health`

### Security

- [ ] API key not in code (use environment variables)
- [ ] Database credentials not in code
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS enabled (use reverse proxy like Nginx)
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] Error messages don't expose sensitive info
- [ ] Logging doesn't capture sensitive data

### Performance

- [ ] Redis caching enabled
- [ ] Database connection pooling configured
- [ ] API rate limits set
- [ ] Load testing completed
- [ ] Response times acceptable
- [ ] Cache hit rate monitored

### Monitoring

- [ ] Logging configured
- [ ] Error tracking enabled (e.g., Sentry)
- [ ] Performance monitoring enabled (e.g., New Relic)
- [ ] Uptime monitoring configured
- [ ] Alerts set up for critical errors
- [ ] Database backups scheduled

### Maintenance

- [ ] Backup strategy in place
- [ ] Update strategy for dependencies
- [ ] Rollback procedure documented
- [ ] Incident response plan
- [ ] Documentation up to date

## Scaling Strategies

### Horizontal Scaling (Multiple Instances)

```yaml
# docker-compose.yml with load balancer
version: '3.8'

services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api1
      - api2
      - api3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api1:
    build: .
    environment:
      REDIS_HOST: redis
    depends_on:
      - redis

  api2:
    build: .
    environment:
      REDIS_HOST: redis
    depends_on:
      - redis

  api3:
    build: .
    environment:
      REDIS_HOST: redis
    depends_on:
      - redis
```

### Vertical Scaling (Larger Instance)

- Increase CPU/RAM allocation
- Increase number of Gunicorn workers
- Increase Redis memory

### Database Optimization

```python
# Add connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'mysql+pymysql://user:password@host/db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## Monitoring & Logging

### Application Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chat_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Performance Monitoring

```python
import time
from functools import wraps

def log_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

@app.post("/chat")
@log_performance
async def chat(request: ChatRequest):
    # ...
```

### Health Checks

```bash
# Regular health check
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "redis": "connected",
  "contexts_loaded": true
}
```

## Backup & Recovery

### Database Backups

```bash
# Backup MariaDB
mysqldump -h 185.49.165.116 -u liontest_user -p vps_liontest_db > backup.sql

# Restore from backup
mysql -h 185.49.165.116 -u liontest_user -p vps_liontest_db < backup.sql
```

### Redis Backups

```bash
# Create Redis snapshot
redis-cli BGSAVE

# Backup RDB file
cp /var/lib/redis/dump.rdb /backup/dump.rdb

# Restore from backup
cp /backup/dump.rdb /var/lib/redis/dump.rdb
redis-cli SHUTDOWN
redis-server
```

### Configuration Backups

```bash
# Backup context files
tar -czf context_backup.tar.gz \
  agent_context_bundle.json \
  fields_context.json \
  query_map.json
```

## Troubleshooting Deployment

### Application Won't Start

```bash
# Check logs
docker-compose logs chat-api

# Common issues:
# 1. Missing environment variables
# 2. Redis not running
# 3. Database unreachable
# 4. Invalid Python syntax
```

### High Memory Usage

```bash
# Check memory
docker stats

# Solutions:
# 1. Increase instance size
# 2. Reduce cache TTL
# 3. Implement memory limits
# 4. Profile code for leaks
```

### Slow Responses

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/chat

# Solutions:
# 1. Check database query performance
# 2. Verify Redis is working
# 3. Check network latency
# 4. Increase instance resources
```

### Database Connection Issues

```bash
# Test connection
mysql -h 185.49.165.116 -u liontest_user -p -e "SELECT 1"

# Solutions:
# 1. Verify credentials
# 2. Check firewall rules
# 3. Verify database is running
# 4. Check network connectivity
```

## Rollback Procedure

### If Deployment Fails

```bash
# Docker
docker-compose down
docker-compose up -d  # Previous version

# Kubernetes
kubectl rollout undo deployment/lion-trans-chat-ai

# Manual
git checkout previous-version
python main.py
```

## Version Management

### Semantic Versioning

```
MAJOR.MINOR.PATCH
1.0.0 = Initial release
1.1.0 = New intent added
1.0.1 = Bug fix
2.0.0 = Breaking changes
```

### Git Tagging

```bash
# Create version tag
git tag -a v1.0.0 -m "Initial release"

# Push tags
git push origin --tags

# Deploy specific version
git checkout v1.0.0
docker build -t lion-trans-chat-ai:v1.0.0 .
```

## Cost Optimization

### Reduce OpenAI API Costs

1. **Increase Cache TTL** (if data freshness allows)
   ```python
   redis_client.setex(cache_key, 7200, ...)  # 2 hours instead of 1
   ```

2. **Use Cheaper Models** (if accuracy allows)
   ```env
   OPENAI_MODEL=gpt-3.5-turbo  # Cheaper than gpt-4o
   ```

3. **Batch Queries**
   ```python
   # Process multiple queries in one API call
   ```

4. **Cache Intent Detection**
   ```python
   # Cache intent detection results
   ```

### Reduce Database Costs

1. **Connection Pooling** - Reuse connections
2. **Query Optimization** - Use indexes
3. **Read Replicas** - Distribute read load
4. **Archive Old Data** - Move to cheaper storage

### Reduce Infrastructure Costs

1. **Use Spot Instances** - 70% cheaper
2. **Serverless** - Pay per request
3. **Reserved Instances** - 40% discount
4. **Right-sizing** - Use appropriate instance size

## Compliance & Security

### Data Protection

- [ ] GDPR compliance (if EU users)
- [ ] Data encryption at rest
- [ ] Data encryption in transit (HTTPS)
- [ ] Regular security audits
- [ ] Penetration testing

### Audit Logging

```python
# Log all queries for audit trail
audit_logger.info(f"User {author_id} queried: {query}")
```

### Access Control

- [ ] API authentication (API keys)
- [ ] Rate limiting per user
- [ ] IP whitelisting
- [ ] Role-based access control

## Disaster Recovery

### RTO/RPO Targets

- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 15 minutes

### Backup Schedule

```bash
# Daily backups
0 2 * * * mysqldump -h 185.49.165.116 -u liontest_user -p vps_liontest_db > /backup/db-$(date +%Y%m%d).sql

# Weekly full backup
0 3 * * 0 tar -czf /backup/full-$(date +%Y%m%d).tar.gz /app

# Monthly archive
0 4 1 * * aws s3 cp /backup s3://lion-trans-backups/$(date +%Y%m)/ --recursive
```

### Recovery Procedure

1. Restore database from backup
2. Restore application files
3. Restart services
4. Verify health checks
5. Run smoke tests

## Conclusion

Deployment checklist:
1. ✅ Choose deployment option
2. ✅ Complete pre-deployment checklist
3. ✅ Set up monitoring
4. ✅ Configure backups
5. ✅ Document procedures
6. ✅ Train team
7. ✅ Deploy with confidence!

For questions, refer to IMPLEMENTATION_GUIDE.md or QUICKSTART.md.
