#!/bin/bash

# NASA Space Biology Engine - AWS Deployment Script
# This script deploys the application to AWS using Docker and ECS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=""
CLUSTER_NAME="nasa-space-biology"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed and configured
check_aws_setup() {
    print_status "Checking AWS CLI setup..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first:"
        print_error "pip install awscli"
        exit 1
    fi
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
    
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "AWS CLI not configured. Run 'aws configure' first."
        exit 1
    fi
    
    print_status "AWS Account ID: $AWS_ACCOUNT_ID"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Create ECR repositories if they don't exist
create_ecr_repos() {
    print_status "Creating ECR repositories..."
    
    repos=("nasa-frontend" "nasa-backend" "nasa-data-pipeline")
    
    for repo in "${repos[@]}"; do
        if aws ecr describe-repositories --repository-names $repo --region $AWS_REGION &> /dev/null; then
            print_warning "Repository $repo already exists"
        else
            print_status "Creating repository: $repo"
            aws ecr create-repository --repository-name $repo --region $AWS_REGION
        fi
    done
}

# Login to ECR
ecr_login() {
    print_status "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
}

# Build and push Docker images
build_and_push() {
    print_status "Building and pushing Docker images..."
    
    # Frontend
    print_status "Building frontend..."
    docker build -t nasa-frontend ./frontend
    docker tag nasa-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-frontend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-frontend:latest
    
    # Backend
    print_status "Building backend..."
    docker build -t nasa-backend ./backend
    docker tag nasa-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-backend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-backend:latest
    
    # Data Pipeline
    print_status "Building data pipeline..."
    docker build -t nasa-data-pipeline ./data-pipeline
    docker tag nasa-data-pipeline:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-data-pipeline:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-data-pipeline:latest
}

# Update task definitions with account ID
update_task_definitions() {
    print_status "Updating task definitions..."
    
    # Update task definition files
    for file in deployment/aws/task-definitions/*.json; do
        sed -i.bak "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" "$file"
        print_status "Updated $(basename $file)"
    done
}

# Create ECS cluster
create_cluster() {
    print_status "Creating ECS cluster..."
    
    if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION &> /dev/null; then
        print_warning "Cluster $CLUSTER_NAME already exists"
    else
        aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
        print_status "Created cluster: $CLUSTER_NAME"
    fi
}

# Register task definitions
register_task_definitions() {
    print_status "Registering task definitions..."
    
    aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definitions/nasa-frontend.json --region $AWS_REGION
    aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definitions/nasa-backend.json --region $AWS_REGION
    aws ecs register-task-definition --cli-input-json file://deployment/aws/task-definitions/nasa-data-pipeline.json --region $AWS_REGION
}

# Create CloudWatch log groups
create_log_groups() {
    print_status "Creating CloudWatch log groups..."
    
    log_groups=("/ecs/nasa-frontend" "/ecs/nasa-backend" "/ecs/nasa-data-pipeline")
    
    for log_group in "${log_groups[@]}"; do
        if aws logs describe-log-groups --log-group-name-prefix $log_group --region $AWS_REGION | grep -q "logGroupName"; then
            print_warning "Log group $log_group already exists"
        else
            aws logs create-log-group --log-group-name $log_group --region $AWS_REGION
            print_status "Created log group: $log_group"
        fi
    done
}

# Display deployment information
show_deployment_info() {
    print_status "Deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Create VPC and subnets for your services"
    echo "2. Create security groups"
    echo "3. Create load balancer"
    echo "4. Create ECS services"
    echo "5. Configure DNS (Route 53)"
    echo ""
    echo "Your ECR repositories:"
    echo "  Frontend: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-frontend"
    echo "  Backend: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-backend"
    echo "  Data Pipeline: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nasa-data-pipeline"
    echo ""
    echo "ECS Cluster: $CLUSTER_NAME"
}

# Main deployment function
deploy() {
    print_status "Starting AWS deployment for NASA Space Biology Engine..."
    
    check_aws_setup
    check_docker
    create_ecr_repos
    ecr_login
    build_and_push
    update_task_definitions
    create_cluster
    create_log_groups
    register_task_definitions
    show_deployment_info
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        check_docker
        ecr_login
        build_and_push
        ;;
    "setup")
        check_aws_setup
        create_ecr_repos
        create_cluster
        create_log_groups
        ;;
    "help")
        echo "Usage: $0 [deploy|build|setup|help]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  build   - Build and push images only"
        echo "  setup   - Setup AWS resources only"
        echo "  help    - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac