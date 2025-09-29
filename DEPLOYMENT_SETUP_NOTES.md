# Fargate Deployment Setup Notes

This document contains step-by-step instructions for setting up and deploying the dot-d-to-nc conversion service to AWS Fargate.

## Prerequisites

### Required Tools
1. **AWS CLI** - Version 2.27.53 or higher
2. **Terraform** - Version 1.5.7 or higher  
3. **Docker** - Version 23.0.5 or higher
4. **Homebrew** (on macOS)

### Installation Commands (macOS)

```bash
# Install Terraform
brew install terraform

# Verify installations
aws --version          # Expected: aws-cli/2.27.53 Python/3.13.5 Darwin/25.0.0 source/arm64
terraform --version    # Expected: Terraform v1.5.7 on darwin_arm64
docker --version       # Expected: Docker version 23.0.5, build bc4487a
```

### AWS Configuration

1. Ensure AWS credentials are properly configured:
   ```bash
   aws configure list
   aws sts get-caller-identity --output json | head -n 10000
   ```

2. Expected output should show your account ID and region (eu-west-2 for London region preference).

## Project Structure

The project contains several deployment-related files:

- `deploy.sh` - Full deployment pipeline (creates infrastructure + deploys app)
- `deploy_fargate.sh` - Updates existing scripts with current AWS account details
- `fargate-infrastructure.tf` - Terraform configuration for AWS resources
- `task-definition.json` - ECS task definition template
- Various `run-*.sh` scripts for executing tasks

## Deployment Process

### Phase 1: Account Configuration Update

1. **Run the account configuration script:**
   ```bash
   ./deploy_fargate.sh
   ```
   
   This script:
   - Detects current AWS account ID (987686461587)
   - Updates all hardcoded account references
   - Creates/updates run scripts with proper values
   - Sets region to eu-west-2 (London)

### Phase 2: Full Infrastructure Deployment

2. **Run the full deployment script:**
   ```bash
   ./deploy.sh
   ```
   
   This script performs:
   - Terraform infrastructure creation (VPC, subnets, security groups, ECS cluster, ECR, S3 buckets, IAM roles)
   - Docker image build and push to ECR
   - ECS task definition registration
   - Test data upload to S3
   - Generation of updated run scripts

## Infrastructure Components Created

### AWS Resources (via Terraform) - ✅ DEPLOYED
- **VPC**: vpc-00c8ebe6caa78c70a (conversion-service-vpc)
- **ECS Cluster**: conversion-service (arn:aws:ecs:eu-west-2:987686461587:cluster/conversion-service)
- **ECR Repository**: 987686461587.dkr.ecr.eu-west-2.amazonaws.com/conversion-service
- **S3 Buckets**: 
  - Input: conversion-service-input-p3m4m5tk
  - Output: conversion-service-output-p3m4m5tk
- **IAM Roles**: 
  - Task Execution: arn:aws:iam::987686461587:role/conversion-service-ecsTaskExecutionRole
  - Task Role: arn:aws:iam::987686461587:role/conversion-service-ecsTaskRole
- **CloudWatch Log Group**: /ecs/conversion-service (30-day retention)
- **Security Groups**: sg-06247b7f954ed8c91 (conversion-service-ecs-tasks)
- **Subnets**: subnet-01ad09a4f268f8a19, subnet-05a566f31bafc362f
- **Task Definition**: arn:aws:ecs:eu-west-2:987686461587:task-definition/conversion-service-task:1

### Generated Files
- `task-definition-final.json`: Final task definition with actual values
- `run-fargate.sh`: Script to run conversion tasks
- Updated configuration files

## Deployment Timeline

**Started:** 2025-09-29T09:55:36Z
**Account ID:** 987686461587  
**Region:** eu-west-2 (London)

### Completed Steps
- ✅ Terraform installation via Homebrew
- ✅ Prerequisites verification (AWS CLI, Terraform, Docker) 
- ✅ Account configuration script execution
- ✅ Infrastructure deployment (18 AWS resources created)
- ✅ Docker image built and pushed to ECR
- ✅ ECS task definition registered
- ⚠️  Test data upload skipped (folder not found)

## Usage After Deployment

### Run Conversion Tasks
```bash
# Using default conversion-service buckets
./run-fargate.sh

# Using custom bucket (two-two-one-b-files-serverless)  
./run-fargate-custom.sh
```

### Monitor Logs
```bash
aws logs tail /ecs/conversion-service --follow --region eu-west-2
```

### Check Results
```bash
# List input bucket contents
aws s3 ls s3://conversion-service-input-[suffix]/ --region eu-west-2

# List output bucket contents  
aws s3 ls s3://conversion-service-output-[suffix]/ --region eu-west-2
```

## Troubleshooting

### Common Issues
1. **Expired AWS Credentials**: Refresh AWS credentials if you see expired token errors
2. **Docker Not Running**: Ensure Docker Desktop is running before deployment
3. **Terraform License Warning**: Version 1.5.7 works despite license change warnings
4. **Missing Output**: Use `| head -n 10000` to capture command output when it goes to screen

### Verification Commands
```bash
# Check ECS clusters
aws ecs list-clusters --output json | head -n 10000

# Check ECR repositories  
aws ecr describe-repositories --region eu-west-2 --output json | head -n 10000

# Check S3 buckets
aws s3 ls --region eu-west-2
```

---

**Note:** This deployment creates resources in AWS that may incur charges. Ensure proper cleanup when no longer needed.

**Last Updated:** 2025-09-29T09:57:08Z