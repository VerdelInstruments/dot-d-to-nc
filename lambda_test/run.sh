#!/bin/bash
#
docker run --rm -it \
  -e AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
  -e AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
  -e AWS_DEFAULT_REGION=$(aws configure get region) \
  -v "$(pwd)/lambda_package:/var/task" \
  -v "$(pwd)/250702_davaoH2O_021.d:/input_data" \
  -w /var/task \
  --memory=29g \
  --platform linux/amd64 \
  baf-linux python3 "lambda_handler.py"


#docker run \
#  -e INPUT_KEY="zipped/250702_davaoH2O_021.d.zip" \
#  -e OUTPUT_BUCKET="output" \
#  new-baf-linux