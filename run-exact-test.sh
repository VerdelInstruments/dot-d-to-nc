#!/bin/bash

# Run the exact command structure you provided
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
          "two-two-one-b-files-serverless",
          "--input-key",
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/46aeb8b1_250702_davaoH2O_021.d/"
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
echo "aws s3 ls s3://two-two-one-b-files-serverless/org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/ --region eu-west-2"
