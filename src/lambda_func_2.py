import json
import os
import mysql.connector
import boto3

S3_BUCKET_NAME = 'ds4300bucket002'
rds_host = 'ds4300db01.cepigam4s00w.us-east-1.rds.amazonaws.com'
rds_user = 'admin'
rds_password = 'JE7EgrBNeycc6dSy'
rds_db_name = 'ds4300db01'
rds_table_name = 'nba_video'

s3_client = boto3.client('s3')

def lambda_handler(event, context):

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        print(f"Processing file: s3://{bucket}/{key}")

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

        if not isinstance(json_data, list):
            json_data = [json_data]

        try:
            conn = mysql.connector.connect(
                host=rds_host, user=rds_user, password=rds_password,
                database=rds_db_name, connect_timeout=10
            )
        except mysql.connector.Error as e:
            return {'statusCode': 500, 'body': f'Error connecting to RDS {e}'}

        if conn.is_connected():
            cursor = conn.cursor()
            try:
                for event_data in json_data:
                    game_id = event_data.get("game_id")
                    event_id = event_data.get("event_id")
                    video = event_data.get("video")
                    video_desc = event_data.get("desc")
                    notes = event_data.get("notes")

                    check_sql = f'SELECT notes FROM {rds_table_name} WHERE game_id = %s AND event_id = %s'
                    cursor.execute(check_sql, (game_id, event_id))
                    existing_notes = cursor.fetchone()

                    if existing_notes:
                        updated_notes = existing_notes[0]
                        if notes:
                            updated_notes = f"{updated_notes}; {notes}"
                        update_sql = f'UPDATE {rds_table_name} SET notes = %s WHERE game_id = %s AND event_id = %s'
                        cursor.execute(update_sql, (updated_notes, game_id, event_id))
                    else:
                        insert_sql = f'INSERT INTO {rds_table_name} (game_id, event_id, video, video_desc, notes) VALUES (%s, %s, %s, %s, %s)'
                        cursor.execute(insert_sql, (game_id, event_id, video, video_desc, notes))

                conn.commit()
                print(f"Processed records in {rds_table_name}")
            except mysql.connector.Error as e:
                print("ERROR: Could not execute database operation.", e)
                conn.rollback()
                return {'statusCode': 500, 'body': 'Error interacting with RDS'}
            finally:
                cursor.close()
                conn.close()

    return {
        'statusCode': 200,
        'body': f'Successfully processed record(s)'
    }