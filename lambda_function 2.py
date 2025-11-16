import boto3
import base64
import datetime
import json

rek = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

STUDENTS_TABLE = "Students"
ATTENDANCE_TABLE = "AttendanceRecords"
FACE_COLLECTION = "students"

students_table = dynamodb.Table(STUDENTS_TABLE)
attendance_table = dynamodb.Table(ATTENDANCE_TABLE)

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"]) if "body" in event else event
        image_data = body.get("Image")
        if not image_data:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing Image"})}

        image_bytes = base64.b64decode(image_data)

        # Search face in Rekognition collection
        response = rek.search_faces_by_image(
            CollectionId=FACE_COLLECTION,
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=90
        )

        if not response['FaceMatches']:
            return {"statusCode": 200, "body": json.dumps({"status": "failed", "message": "Face not recognized"})}

        face_id = response['FaceMatches'][0]['Face']['FaceId']

        # Lookup student by FaceId
        result = students_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('FaceId').eq(face_id)
        )

        if not result['Items']:
            return {"statusCode": 200, "body": json.dumps({"status": "failed", "message": "Student not found"})}

        student = result['Items'][0]

        # Mark attendance
        attendance_table.put_item(Item={
            'UserId': student['StudentId'],
            'Timestamp': datetime.datetime.now().isoformat()
        })

        return {"statusCode": 200, "body": json.dumps({"status": "success", "message": f"Attendance marked for {student['Name']}"})}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
