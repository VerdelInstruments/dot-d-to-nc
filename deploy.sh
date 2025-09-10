#!/bin/bash

set -e

# Configuration
AWS_REGION=${AWS_REGION:-"eu-west-2"}
PROJECT_NAME="conversion-service"

echo "🚀 Starting deployment to AWS Fargate..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install it first."
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# Step 1: Deploy infrastructure with Terraform
echo "🏗️  Deploying infrastructure..."
terraform init
terraform plan -var="aws_region=$AWS_REGION"
terraform apply -var="aws_region=$AWS_REGION" -auto-approve

# Get Terraform outputs
ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
INPUT_BUCKET=$(terraform output -raw input_bucket_name)
OUTPUT_BUCKET=$(terraform output -raw output_bucket_name)
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SUBNET_IDS=$(terraform output -json subnet_ids | jq -r '.[]' | paste -sd "," -)
SECURITY_GROUP_ID=$(terraform output -raw security_group_id)
TASK_EXECUTION_ROLE_ARN=$(terraform output -raw task_execution_role_arn)
TASK_ROLE_ARN=$(terraform output -raw task_role_arn)

echo "📦 ECR Repository: $ECR_REPO_URL"
echo "📥 Input Bucket: $INPUT_BUCKET"
echo "📤 Output Bucket: $OUTPUT_BUCKET"

# Step 2: Build and push Docker image
echo "🐳 Building and pushing Docker image..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL

# Build the image for AMD64 architecture (required for Fargate)
docker buildx build --platform linux/amd64 -t $PROJECT_NAME .

# Tag and push
docker tag $PROJECT_NAME:latest $ECR_REPO_URL:latest
docker push $ECR_REPO_URL:latest

echo "✅ Docker image pushed successfully"

# Step 3: Create updated task definition
echo "📋 Creating ECS task definition..."

# Update task definition with actual values
cat > task-definition-final.json << EOF
{
  "family": "$PROJECT_NAME-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "30720",
  "executionRoleArn": "$TASK_EXECUTION_ROLE_ARN",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "$PROJECT_NAME",
      "image": "$ECR_REPO_URL:latest",
      "cpu": 4096,
      "memory": 30720,
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$PROJECT_NAME",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "INPUT_BUCKET",
          "value": "$INPUT_BUCKET"
        },
        {
          "name": "OUTPUT_BUCKET",
          "value": "$OUTPUT_BUCKET"
        },
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "$AWS_REGION"
        }
      ]
    }
  ]
}
EOF

# Register task definition
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
  --cli-input-json file://task-definition-final.json \
  --region $AWS_REGION \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "✅ Task definition registered: $TASK_DEFINITION_ARN"

# Step 4: Upload test data to S3
echo "📂 Uploading test data to S3..."
aws s3 sync "250702_davaoH2O_021.d/" "s3://$INPUT_BUCKET/250702_davaoH2O_021.d/" --region $AWS_REGION

echo "✅ Test data uploaded to s3://$INPUT_BUCKET/250702_davaoH2O_021.d/"

# Step 5: Create run script for Fargate
cat > run-fargate.sh << EOF
#!/bin/bash

# Run the conversion task on AWS Fargate
aws ecs run-task \\
  --cluster $CLUSTER_NAME \\
  --task-definition $TASK_DEFINITION_ARN \\
  --launch-type FARGATE \\
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \\
  --overrides '{
    "containerOverrides": [
      {
        "name": "$PROJECT_NAME",
        "command": [
          "python3",
          "extract_s3.py",
          "--input-bucket",
          "$INPUT_BUCKET",
          "--output-bucket", 
          "$OUTPUT_BUCKET",
          "--input-key",
          "250702_davaoH2O_021.d/"
        ]
      }
    ]
  }' \\
  --region $AWS_REGION
EOF

chmod +x run-fargate.sh

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Run the conversion task: ./run-fargate.sh"
echo "2. Monitor logs: aws logs tail /ecs/$PROJECT_NAME --follow --region $AWS_REGION"
echo "3. Check output: aws s3 ls s3://$OUTPUT_BUCKET/ --region $AWS_REGION"
echo ""
echo "Resources created:"
echo "- ECS Cluster: $CLUSTER_NAME"
echo "- ECR Repository: $ECR_REPO_URL"
echo "- Input S3 Bucket: s3://$INPUT_BUCKET"
echo "- Output S3 Bucket: s3://$OUTPUT_BUCKET"
echo ""
