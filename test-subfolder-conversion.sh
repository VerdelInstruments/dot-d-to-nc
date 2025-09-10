#!/bin/bash

# Configuration - UPDATE THESE VALUES
FOLDER_ID="org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6"
D_FILE_NAME="your-actual-file.d"  # Replace with your actual .d file name

# Run the conversion task on AWS Fargate with subfolder paths
aws ecs run-task \
  --cluster conversion-service \
  --task-definition arn:aws:ecs:eu-west-2:403759282768:task-definition/conversion-service-task:3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-07036a9a493e5eb1e,subnet-0c23d29e9aaaf1fa2],securityGroups=[sg-0f06f25b1f621f82c],assignPublicIp=ENABLED}" \
  --overrides '{
    "containerOverrides": [
      {
        "name": "conversion-service",
        "command": [
          "python3",
          "extract_s3.py",
          "--input-bucket",
          "two-two-one-b-files-serverless",
          "--output-bucket", 
          "conversion-service-output-7v5plwgs",
          "--input-key",
          "'$FOLDER_ID'/'$D_FILE_NAME'/",
          "--output-key",
          "'$FOLDER_ID'/'$D_FILE_NAME'_converted.nc"
        ]
      }
    ]
  }' \
  --region eu-west-2

echo ""
echo "Task submitted! Monitor with:"
echo "aws logs tail /ecs/conversion-service --follow --region eu-west-2"
echo ""
echo "Check output with:"
echo "aws s3 ls s3://conversion-service-output-7v5plwgs/$FOLDER_ID/ --region eu-west-2"
