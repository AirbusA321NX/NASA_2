# NASA Space Biology Engine - AWS ECS Deployment Guide

This guide covers deploying the NASA Space Biology Knowledge Engine to AWS using ECS (Elastic Container Service) with ECR (Elastic Container Registry).

## Prerequisites

1. **AWS CLI installed and configured**
```bash
pip install awscli
aws configure
```

2. **Docker installed and running**

3. **AWS account with appropriate permissions**

## Option 1: Quick Deploy with Elastic Beanstalk (Recommended for students/demos)

### Step 1: Prepare simplified app
```bash
# Create a simple single-container version
cd frontend
npm run build
cd ..

# Create application.zip with built frontend
zip -r application.zip frontend/out backend data-pipeline package.json
```

### Step 2: Deploy to Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli --upgrade

# Initialize EB application
eb init nasa-space-biology --platform "Node.js 18" --region us-east-1

# Create environment and deploy
eb create nasa-dashboard-prod --cname nasa-space-biology

# Deploy updates
eb deploy
```

### Step 3: Configure environment variables
```bash
# Set environment variables
eb setenv MISTRAL_API_KEY=your-mistral-key
eb setenv NODE_ENV=production
eb setenv NEXT_PUBLIC_API_URL=https://nasa-space-biology.elasticbeanstalk.com
```

Your app will be available at: `https://nasa-space-biology.elasticbeanstalk.com`

## Option 2: Full Production Deploy with ECS/ECR (Recommended for production)

### Step 1: Create ECR repositories
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name nasa-frontend --region us-east-1
aws ecr create-repository --repository-name nasa-backend --region us-east-1  
aws ecr create-repository --repository-name nasa-data-pipeline --region us-east-1
```

### Step 2: Build and push Docker images
```bash
# Frontend
docker build -t nasa-frontend ./frontend
docker tag nasa-frontend:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/nasa-frontend:latest
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/nasa-frontend:latest

# Backend  
docker build -t nasa-backend ./backend
docker tag nasa-backend:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/nasa-backend:latest
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/nasa-backend:latest

# Data Pipeline
docker build -t nasa-data-pipeline ./data-pipeline  
docker tag nasa-data-pipeline:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/nasa-data-pipeline:latest
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/nasa-data-pipeline:latest
```

### Step 3: Create ECS Cluster
```bash
# Create cluster
aws ecs create-cluster --cluster-name nasa-space-biology

# Create task definitions (see task-definitions/ folder)
aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definitions/nasa-frontend.json
aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definitions/nasa-backend.json
aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definitions/nasa-data-pipeline.json
```

### Step 4: Create services
```bash
# Create services with load balancer
aws ecs create-service --cluster nasa-space-biology --service-name nasa-frontend --task-definition nasa-frontend --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Option 3: Simple EC2 Deployment

### Step 1: Launch EC2 instance
1. Go to AWS Console → EC2
2. Launch new instance (t3.medium recommended)
3. Choose Ubuntu 22.04 LTS
4. Create key pair for SSH access
5. Configure security group (ports 80, 443, 22, 3000, 4000, 8001)

### Step 2: Connect and setup
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install dependencies
sudo apt update
sudo apt install -y docker.io docker-compose nodejs npm python3 python3-pip
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Clone your repository
git clone https://github.com/your-username/nasa-space-biology-engine
cd nasa-space-biology-engine
```

### Step 3: Deploy with Docker Compose
```bash
# Set environment variables
cp .env.example .env
# Edit .env with your values

# Deploy
docker-compose -f deployment/aws/docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

Your app will be available at: `http://your-ec2-ip:3000`

## Environment Variables Required

Create a `.env` file with these variables:

```bash
# API Keys
MISTRAL_API_KEY=your-mistral-api-key

# Database
POSTGRES_DB=nasa_biology
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://postgres:your-secure-password@postgres:5432/nasa_biology

# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_URI=bolt://neo4j:7687

# Redis
REDIS_URL=redis://redis:6379

# AWS (if using S3 for data storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# App URLs
API_URL=https://your-backend-url.com
```

## Monitoring and Logs

### CloudWatch Logs (for ECS)
```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/nasa-frontend
aws logs create-log-group --log-group-name /ecs/nasa-backend
aws logs create-log-group --log-group-name /ecs/nasa-data-pipeline
```

### Check application health
```bash
# Test endpoints
curl https://your-app-url.com/health
curl https://your-app-url.com/api/health
curl https://your-app-url.com/api/data/health
```

## Cost Optimization

### For Students/Demos:
- Use **Elastic Beanstalk** with t3.micro instances (free tier)
- Use **RDS free tier** for PostgreSQL
- Use **ElastiCache free tier** for Redis

### For Production:
- Use **ECS Fargate** with auto-scaling
- Use **RDS with Multi-AZ** for reliability
- Use **CloudFront CDN** for frontend
- Use **Application Load Balancer** for high availability

## Troubleshooting

### Common Issues:

1. **Container fails to start**
```bash
# Check logs
docker logs container-name
aws logs describe-log-streams --log-group-name /ecs/nasa-frontend
```

2. **Database connection fails**
```bash
# Check security groups allow port 5432
# Verify environment variables
# Test connection manually
```

3. **Frontend can't reach backend**
```bash
# Check CORS settings in backend
# Verify API_URL environment variable
# Check security group rules
```

## Security Best Practices

1. **Use IAM roles** instead of access keys when possible
2. **Enable CloudTrail** for audit logging  
3. **Use VPC** with private subnets for databases
4. **Enable SSL/TLS** with Certificate Manager
5. **Use AWS Secrets Manager** for sensitive data
6. **Enable backup** for RDS and EFS volumes

## Scaling

### Horizontal Scaling:
```bash
# Update service desired count
aws ecs update-service --cluster nasa-space-biology --service nasa-frontend --desired-count 3
```

### Auto Scaling:
- Configure **Application Auto Scaling** for ECS services
- Set up **CloudWatch alarms** for CPU/memory thresholds
- Use **Target Tracking Scaling** policies

---

## Quick Commands Reference

```bash
# Deploy to Elastic Beanstalk
eb create nasa-dashboard --cname nasa-space-biology
eb deploy

# Deploy to ECS
docker-compose -f deployment/aws/docker-compose.prod.yml up -d

# Check status
eb status
docker-compose ps
aws ecs describe-services --cluster nasa-space-biology
```

Choose the deployment option that best fits your needs:
- **Elastic Beanstalk**: Easiest for demos and prototypes
- **ECS/ECR**: Best for production and scalability  
- **EC2**: Most control and cost-effective for small teams