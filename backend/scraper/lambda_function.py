# backend\batch\lambda_function.py

import json

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from Lambda!"})
    }
