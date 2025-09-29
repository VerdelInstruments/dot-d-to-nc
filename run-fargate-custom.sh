#!/bin/bash

# Run the conversion task on AWS Fargate with custom bucket
aws ecs run-task \
  --cluster conversion-service \
  --task-definition arn:aws:ecs:eu-west-2:987686461587:task-definition/conversion-service-task:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-01ad09a4f268f8a19,subnet-05a566f31bafc362f],securityGroups=[sg-06247b7f954ed8c91],assignPublicIp=ENABLED}" \
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
          "conversion-service-output-p3m4m5tk",
          "--input-key",
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/your-file.d/",
          "--output-key",
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/converted_output.nc"
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
