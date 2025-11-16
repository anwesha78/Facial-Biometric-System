import boto3
import base64
import uuid
from datetime import datetime

rek = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

STUDENTS_TABLE = "Students"
S3_BUCKET = "facial-attendance-anwesha"
FACE_COLLECTION = "students"

students_table = dynamodb.Table(STUDENTS_TABLE)

def lambda_handler(event, context):
    try:
        body = event
        if "body" in event:
            import json
            body = json.loads(event["body"])

        student_id = body.get("StudentId")
        name = body.get("Name")
        image_data = body.get("Image")

        if not student_id or not name or not image_data:
            return {"statusCode": 400, "body": '{"error":"Missing fields: StudentId, Name, Image"}'}

        image_bytes = base64.b64decode(image_data)

        # 1️⃣ Upload to S3
        s3.put_object(Bucket=S3_BUCKET, Key=f"{student_id}.jpg", Body=image_bytes, ContentType="image/jpeg")

        # 2️⃣ Add to Rekognition
        response = rek.index_faces(
            CollectionId=FACE_COLLECTION,
            Image={'Bytes': image_bytes},
            ExternalImageId=student_id,
            DetectionAttributes=['DEFAULT']
        )

        if not response['FaceRecords']:
            return {"statusCode": 400, "body": '{"error":"No face detected"}'}

        face_id = response['FaceRecords'][0]['Face']['FaceId']

        # 3️⃣ Add to DynamoDB
        students_table.put_item(Item={
            'StudentId': student_id,
            'Name': name,
            'FaceId': face_id
        })

        return {"statusCode": 200, "body": f'{{"status":"success","message":"Student {name} registered successfully"}}'}

    except Exception as e:
        return {"statusCode": 500, "body": f'{{"error":"{str(e)}"}}'}
