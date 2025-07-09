import boto3 

def deploy_lambda(function_name, role_arn, zip_file_path):

    lambda_client = boto3.client('lambda')

    with open(zip_file_path, 'rb') as f:
        content = f.read()

    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={"ZipFile": content},
        Timeout=30,
        MemorySize=128,
        Publish=True
    )

    print(f"Lambda function {function_name} created successfully.")
    print(response)


if __name__ == '__main__':
    deploy_lambda(
        function_name='verdel_lambda_function',
        role_arn='arn:aws:iam::680346249802:role/lambda-s3-role',  # Replace with your actual role ARN
        zip_file_path='lambda_function.zip'  # Path to your zipped Lambda function code
    )