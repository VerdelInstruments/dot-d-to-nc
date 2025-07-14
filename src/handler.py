from extract import extract_data

def lambda_handler(event, context):
    """
    AWS Lambda handler function to process incoming events.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (LambdaContext): The runtime information of the Lambda function.

    Returns:
        dict: A response object containing the status code and message.
    """
    print("Received event:", event)


    d_directory = event.get('d_directory')
    save_location = event.get("save_location")

    print(d_directory)
    result = extract_data(
        d_directory=d_directory,
        save_location=save_location
    )

    return {
        'statusCode': 200,
        'body': 'Completed',
        'location': result
    }

if __name__ == '__main__':
    lambda_handler({"d_directory": "/input_data", "save_location": "/var/task/out"}, '')
