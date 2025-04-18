# lambda_log_to_rds.py
import json
import pymysql
import os

def lambda_handler(event, context):
    body = json.loads(event['body'])

    conn = pymysql.connect(
        host=os.environ['RDS_HOST'],
        user=os.environ['RDS_USER'],
        password=os.environ['RDS_PASS'],
        db=os.environ['RDS_DB']
    )

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO fitness_logs (date, weight, meal, workout, image_filename)
            VALUES (%s, %s, %s, %s, %s)
        """, (body['date'], body['weight'], body['meal'], body['workout'], body['image_filename']))
        conn.commit()

    return {
        'statusCode': 200,
        'body': json.dumps('Log stored successfully!')
    }
