#!/bin/bash

set -e

# Configuration
AWS_REGION=${AWS_REGION:-"eu-west-2"}
PROJECT_NAME="conversion-service"

echo "🚀 Updating Fargate deployment scripts with current AWS account configuration..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Get current AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CURRENT_REGION=$(aws configure get region || echo $AWS_REGION)

echo "📋 Current AWS Account ID: $AWS_ACCOUNT_ID"
echo "📋 Using AWS Region: $CURRENT_REGION"

# Get existing ECS infrastructure details
echo "🔍 Discovering existing ECS infrastructure..."

# Find the ECS cluster
CLUSTER_NAME=$(aws ecs list-clusters --query 'clusterArns[?contains(@, `conversion-service`)][0]' --output text --region $CURRENT_REGION | sed 's|.*/||' || echo "conversion-service")
if [ "$CLUSTER_NAME" = "None" ] || [ -z "$CLUSTER_NAME" ]; then
    CLUSTER_NAME="conversion-service"
fi

# Find the latest task definition
TASK_DEF_ARN=$(aws ecs list-task-definitions --family-prefix "$PROJECT_NAME-task" --status ACTIVE --sort DESC --query 'taskDefinitionArns[0]' --output text --region $CURRENT_REGION 2>/dev/null || echo "")

if [ "$TASK_DEF_ARN" = "None" ] || [ -z "$TASK_DEF_ARN" ]; then
    echo "⚠️  No existing task definition found. You may need to run the full deployment first."
    # Construct likely task definition ARN
    TASK_DEF_ARN="arn:aws:ecs:$CURRENT_REGION:$AWS_ACCOUNT_ID:task-definition/$PROJECT_NAME-task:3"
fi

# Find existing subnets and security groups
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=$PROJECT_NAME-vpc" --query 'Vpcs[0].VpcId' --output text --region $CURRENT_REGION 2>/dev/null || echo "")

if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    echo "⚠️  No VPC found with name $PROJECT_NAME-vpc. Using hardcoded values."
    SUBNET_IDS="subnet-07036a9a493e5eb1e,subnet-0c23d29e9aaaf1fa2"
    SECURITY_GROUP_ID="sg-0f06f25b1f621f82c"
else
    # Get subnet IDs
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=$PROJECT_NAME-public-*" --query 'Subnets[].SubnetId' --output text --region $CURRENT_REGION | tr '\t' ',')
    
    # Get security group ID
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=$PROJECT_NAME-ecs-tasks" --query 'SecurityGroups[0].GroupId' --output text --region $CURRENT_REGION)
    
    if [ "$SUBNET_IDS" = "None" ] || [ -z "$SUBNET_IDS" ]; then
        echo "⚠️  Could not find subnets. Using hardcoded values."
        SUBNET_IDS="subnet-07036a9a493e5eb1e,subnet-0c23d29e9aaaf1fa2"
    fi
    
    if [ "$SECURITY_GROUP_ID" = "None" ] || [ -z "$SECURITY_GROUP_ID" ]; then
        echo "⚠️  Could not find security group. Using hardcoded value."
        SECURITY_GROUP_ID="sg-0f06f25b1f621f82c"
    fi
fi

# Find existing S3 buckets
INPUT_BUCKET=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'conversion-service-input')].Name" --output text --region $CURRENT_REGION | head -n1 || echo "conversion-service-input-7v5plwgs")
OUTPUT_BUCKET=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'conversion-service-output')].Name" --output text --region $CURRENT_REGION | head -n1 || echo "conversion-service-output-7v5plwgs")

if [ -z "$INPUT_BUCKET" ]; then
    INPUT_BUCKET="conversion-service-input-7v5plwgs"
fi

if [ -z "$OUTPUT_BUCKET" ]; then
    OUTPUT_BUCKET="conversion-service-output-7v5plwgs"
fi

echo "📦 Infrastructure Details:"
echo "  - ECS Cluster: $CLUSTER_NAME"
echo "  - Task Definition: $TASK_DEF_ARN"
echo "  - Subnets: $SUBNET_IDS"
echo "  - Security Group: $SECURITY_GROUP_ID"
echo "  - Input Bucket: $INPUT_BUCKET"
echo "  - Output Bucket: $OUTPUT_BUCKET"

# Update run-fargate.sh with current values
echo "🔧 Updating run-fargate.sh..."
cat > run-fargate.sh << EOF
#!/bin/bash

# Run the conversion task on AWS Fargate
aws ecs run-task \\
  --cluster $CLUSTER_NAME \\
  --task-definition $TASK_DEF_ARN \\
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
  --region $CURRENT_REGION
EOF

chmod +x run-fargate.sh

# Create additional run scripts for different scenarios

# Script for custom bucket usage (like two-two-one-b-files-serverless)
echo "🔧 Creating run-fargate-custom.sh..."
cat > run-fargate-custom.sh << EOF
#!/bin/bash

# Run the conversion task on AWS Fargate with custom bucket
aws ecs run-task \\
  --cluster $CLUSTER_NAME \\
  --task-definition $TASK_DEF_ARN \\
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
          "two-two-one-b-files-serverless",
          "--output-bucket", 
          "$OUTPUT_BUCKET",
          "--input-key",
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/your-file.d/",
          "--output-key",
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/converted_output.nc"
        ]
      }
    ]
  }' \\
  --region $CURRENT_REGION

echo ""
echo "Task submitted! Monitor with:"
echo "aws logs tail /ecs/$PROJECT_NAME --follow --region $CURRENT_REGION"
echo ""
echo "Check output with:"
echo "aws s3 ls s3://two-two-one-b-files-serverless/org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/ --region $CURRENT_REGION"
EOF

chmod +x run-fargate-custom.sh

# Update task-definition.json template with current account details
echo "🔧 Updating task-definition.json template..."
if [ -f "task-definition.json" ]; then
    # Create a backup
    cp task-definition.json task-definition.json.bak
    
    # Update the template with actual account ID and region
    sed -i.tmp "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-definition.json
    sed -i.tmp "s/YOUR_REGION/$CURRENT_REGION/g" task-definition.json
    sed -i.tmp "s/YOUR_INPUT_BUCKET/$INPUT_BUCKET/g" task-definition.json
    sed -i.tmp "s/YOUR_OUTPUT_BUCKET/$OUTPUT_BUCKET/g" task-definition.json
    
    # Remove temporary file
    rm -f task-definition.json.tmp
    
    echo "✅ Updated task-definition.json with current account values"
fi

echo ""
echo "✅ Deployment scripts updated successfully!"
echo ""
echo "Available scripts:"
echo "  - run-fargate.sh: Run with default conversion-service buckets"
echo "  - run-fargate-custom.sh: Run with custom bucket (two-two-one-b-files-serverless)"
echo ""
echo "To run a conversion task:"
echo "  ./run-fargate.sh"
echo ""
echo "To monitor logs:"
echo "  aws logs tail /ecs/$PROJECT_NAME --follow --region $CURRENT_REGION"
echo ""
echo "To check buckets:"
echo "  aws s3 ls s3://$INPUT_BUCKET/ --region $CURRENT_REGION"
echo "  aws s3 ls s3://$OUTPUT_BUCKET/ --region $CURRENT_REGION"