import boto3
import io

s3_client = boto3.client("s3")
textract_client = boto3.client("textract")
DEST_BUCKET = "ds4300bucket02"

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            file_content = obj['Body'].read()
        except s3_client.exceptions.NoSuchKey:
            print(f"File not found: s3://{bucket}/{key}")
            continue

        filename = key.split('/')[-1]
        processed_image_key = f"{filename}"

        s3_client.put_object(
            Bucket=DEST_BUCKET,
            Key=processed_image_key,
            Body=file_content,
            ContentType=obj.get('ContentType', 'application/octet-stream')
        )

        text_filename = f"{filename.rsplit('.', 1)[0]}.txt"
        processed_text_key = f"processed_text/{text_filename}"
        
        response = textract_client.detect_document_text(
            Document={'Bytes': file_content}
        )

        extracted_text = ""
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                extracted_text += item["Text"] + "\n"

        print(f"Extracted text from {key}:")
        print(extracted_text)

        s3_client.put_object(
            Bucket=DEST_BUCKET,
            Key=processed_text_key,
            Body=extracted_text.encode('utf-8'),
            ContentType='text/plain'
        )

        print(f"Saved extracted text as {processed_text_key}")

    return {
        'statusCode': 200,
        'body': 'Images and text processed successfully'
    }
