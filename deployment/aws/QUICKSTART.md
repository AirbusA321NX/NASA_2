# NASA Space Biology Engine - Quick Start Scripts

# Make scripts executable
chmod +x deployment/aws/deploy.sh
chmod +x deployment/aws/scripts/*.sh

# ============================================
# Option 1: Elastic Beanstalk (Easiest)
# ============================================

# 1. Install EB CLI
pip install awsebcli --upgrade

# 2. Configure AWS credentials
aws configure

# 3. Initialize and deploy
eb init nasa-space-biology --platform "Node.js 18" --region us-east-1
eb create nasa-dashboard-prod --cname nasa-space-biology
eb setenv MISTRAL_API_KEY=your-key NODE_ENV=production

# Your app will be at: https://nasa-space-biology.elasticbeanstalk.com

# ============================================
# Option 2: Docker + ECS (Production)
# ============================================

# 1. Set up AWS resources
./deployment/aws/deploy.sh setup

# 2. Build and push images  
./deployment/aws/deploy.sh build

# 3. Deploy to ECS
./deployment/aws/deploy.sh deploy

# ============================================
# Option 3: Simple EC2 (Manual)
# ============================================

# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install -y docker.io docker-compose nodejs npm python3 python3-pip
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# 4. Clone and deploy
git clone https://github.com/your-username/nasa-space-biology-engine
cd nasa-space-biology-engine
cp deployment/aws/.env.example .env
# Edit .env with your values
docker-compose -f deployment/aws/docker-compose.prod.yml up -d

# Your app will be at: http://your-ec2-ip:3000

# ============================================
# Quick Commands
# ============================================

# Check deployment status
eb status                                    # Elastic Beanstalk
docker-compose ps                           # Docker Compose
aws ecs describe-services --cluster nasa-space-biology  # ECS

# View logs
eb logs                                     # Elastic Beanstalk
docker-compose logs                         # Docker Compose
aws logs tail /ecs/nasa-frontend           # CloudWatch

# Update deployment
eb deploy                                   # Elastic Beanstalk
docker-compose -f deployment/aws/docker-compose.prod.yml up -d  # Docker Compose
./deployment/aws/deploy.sh build           # ECS

# ============================================
# Troubleshooting
# ============================================

# Common issues:
# 1. CORS errors: Check NEXT_PUBLIC_API_URL in frontend
# 2. Database connection: Verify DATABASE_URL and security groups
# 3. Container crashes: Check logs with commands above
# 4. 502/503 errors: Verify health check endpoints

# Test endpoints:
curl https://your-app-url.com/health
curl https://your-app-url.com/api/health
curl https://your-app-url.com/api/data/health