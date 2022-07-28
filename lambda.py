### FIRST LAMBDA FUNCTION ###

import json
import boto3
import base64

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event["s3_bucket"]
    
    # Download the data from s3 to /tmp/image.png
    s3.Bucket(
        bucket
    ).download_file(
        key,
        "/tmp/image.png"
    )
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

### SECOND LAMBDA FUNCTION ###

import json
import base64
import boto3
import io

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2022-07-19-16-43-04-046"
runtime=boto3.client("runtime.sagemaker")

def lambda_handler(event, context):

    # Decode the image data
    image = base64.b64decode(event["body"]["image_data"])

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT,
        ContentType="image/png",
        Body=image
    )
    
    inferences = json.loads(response["Body"].read().decode())

    # We return the data back to the Step Function    
    #event["inferences"] = inferences.decode('utf-8')
    event["body"]["inferences"] = inferences
    
    print(event)
    
    return {
        'statusCode': 200,
        'body': event["body"]
    }

### THIRD LAMBDA FUNCTION ###

import json


THRESHOLD = .93


def lambda_handler(event, context):

    # Grab the inferences from the event
    inferences = event["body"]["inferences"]

    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = inferences[0] >= THRESHOLD \
        or inferences[1] >= THRESHOLD

    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': event["body"]
    }