import json
import boto3
import re

S3_BUCKET_NAME = 'ds4300bucket001'
S3_BUCKET_DEST = 'ds4300bucket002'
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            file_content = obj['Body'].read().decode('utf-8')
        except s3_client.exceptions.NoSuchKey:
            print(f"File not found: s3://{bucket}/{key}")
            continue
        except Exception as e:
            print(f"Error getting object s3://{bucket}/{key}: {e}")
            continue

        try:
            json_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from s3://{bucket}/{key}: {e}")
            continue

        note = json_data.get('notes', '')
        if isinstance(note, str):
            note = note.strip()
            note = re.sub(r'\s+', ' ', note)
            note = re.sub(r'[^\w\s.,!?]', '', note)
        
        json_data['notes'] = note

        try:
            s3_client.put_object(
                Bucket=S3_BUCKET_DEST,
                Key=key,
                Body=json.dumps(json_data),
                ContentType='application/json'
            )
            print(f"Successfully processed s3://{bucket}/{key} and uploaded to s3://{S3_BUCKET_DEST}/{key}")
        except Exception as e:
            print(f"Error putting object to s3://{S3_BUCKET_DEST}/{key}: {e}")

    return {
        'statusCode': 200,
        'body': 'JSON processing completed'
    }