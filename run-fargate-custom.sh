#!/bin/bash

# Run the conversion task on AWS Fargate with custom bucket
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
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/your-file.d/",
          "--output-key",
          "org-bda1752a-5cc4-4ac2-b207-8a85d09f80e6/converted_output.nc"
        ]
      }
    ]
  }' \
  --region eu-west-2
