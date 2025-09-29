#!/bin/bash

# Run the conversion task on AWS Fargate
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
          "conversion-service-input-p3m4m5tk",
          "--output-bucket", 
          "conversion-service-output-p3m4m5tk",
          "--input-key",
          "250702_davaoH2O_021.d/"
        ]
      }
    ]
  }' \
  --region eu-west-2
