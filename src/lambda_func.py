import json
import boto3

S3_BUCKET_NAME = 'ds4300bucket01'
S3_BUCKET_DEST = 'ds4300bucket02'
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        try:
            obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
            file_content = obj['Body'].read().decode('utf-8')
        except s3_client.exceptions.NoSuchKey:
            print(f"File not found: s3://{bucket}/{key}")
            continue

        json_data = json.loads(file_content)
        cleaned_data = []
        for item in json_data:
            cleaned_item = {key.lower(): value for key, value in item.items()}
            cleaned_data.append(cleaned_item)

        s3_client.put_object(
            Bucket=S3_BUCKET_DEST,
            Key=key,
            Body=json.dumps(cleaned_data),
            ContentType='text/plain'
        )


    return {
        'statusCode': 200,
        'body': 'Images and text processed successfully'
    }