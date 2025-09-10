#!/bin/bash

# Run the conversion task on AWS Fargate
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
          "conversion-service-input-7v5plwgs",
          "--output-bucket", 
          "conversion-service-output-7v5plwgs",
          "--input-key",
          "250702_davaoH2O_021.d/"
        ]
      }
    ]
  }' \
  --region eu-west-2
