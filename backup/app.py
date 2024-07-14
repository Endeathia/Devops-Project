import threading
import time
from pathlib import Path
from detect import run
import yaml
from loguru import logger
import os
import boto3
import requests
import json
from decimal import Decimal
import sys
import signal
from flask import Flask

# Flask app for health checks
app = Flask(__name__)

# Environment variables
images_bucket = os.getenv('BUCKET_NAME')
queue_name = os.getenv('SQS_QUEUE_NAME')
region_name = os.getenv('AWS_REGION', 'us-east-1')
dynamodb_region = os.getenv('DYNAMODB_REGION', 'us-west-1')

# Validate environment variables
if not images_bucket or not queue_name:
    logger.error("BUCKET_NAME and SQS_QUEUE_NAME environment variables are required")
    sys.exit(1)

sqs_client = boto3.client('sqs', region_name=region_name)
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name=dynamodb_region)
table_name = 'Yolo-Project'
table = dynamodb.Table(table_name)

# Load coco names
with open("data/coco128.yaml", "rb") as stream:
    names = yaml.safe_load(stream)['names']

# Handle SIGTERM for graceful shutdown
def handle_sigterm(*args):
    print("Received SIGTERM. Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

def all_required_services_are_running():
    # Perform actual checks to ensure required services are running
    return True

@app.route('/liveness')
def liveness():
    if all_required_services_are_running():
        return 'OK', 200
    else:
        return 'Service Unavailable', 500

@app.route('/readiness')
def readiness():
    if all_required_services_are_running():
        return 'Ready', 200
    else:
        return 'Service Unavailable', 500

def consume():
    logger.info("Starting message consumption...")
    while True:
        try:
            response = sqs_client.receive_message(QueueUrl=queue_name, MaxNumberOfMessages=1, WaitTimeSeconds=5)
            logger.info(response)
        except Exception as e:
            logger.error(f"Failed to receive message from SQS. Error: {e}")
            time.sleep(5)  # Wait before retrying
            continue

        if 'Messages' in response:
            message_body = response['Messages'][0]['Body']
            try:
                message = json.loads(message_body)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON message: {e}")
                continue

            receipt_handle = response['Messages'][0]['ReceiptHandle']
            prediction_id = response['Messages'][0]['MessageId']

            logger.info(f'prediction: {prediction_id}. start processing')

            if not os.path.exists('downloads'):
                os.mkdir('downloads')
            img_name = message.get('photo_key')
            chat_id = message.get('chat_id')
            original_img_path = f"downloads/{img_name}"

            if not img_name:
                logger.error("Message does not contain 'photo_key'")
                continue

            try:
                logger.info(f'Downloading {img_name} from bucket {images_bucket}')
                s3.download_file(images_bucket, img_name, original_img_path)
                logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')
            except Exception as e:
                logger.error(f'Failed to download {img_name} from bucket {images_bucket}. Error: {e}')
                continue

            try:
                run(
                    weights='yolov5s.pt',
                    data='data/coco128.yaml',
                    source=original_img_path,
                    project='static/data',
                    name=prediction_id,
                    save_txt=True
                )
                logger.info(f'prediction: {prediction_id}/{original_img_path}. Prediction done')
            except Exception as e:
                logger.error(f'Prediction failed for {original_img_path}. Error: {e}')
                continue

            predicted_img_dir = Path(f'static/data/{prediction_id}')
            predicted_img_path = predicted_img_dir / img_name
            predicted_img_path_str = str(predicted_img_path)
            logger.info(f'Predicted image path: {predicted_img_path_str}')

            try:
                if os.path.isfile(predicted_img_path_str):
                    logger.info(f'Uploading {predicted_img_path_str} to bucket {images_bucket}')
                    s3.upload_file(predicted_img_path_str, images_bucket, os.path.basename(predicted_img_path_str))
                    logger.info(f'File {predicted_img_path_str} uploaded successfully to {images_bucket}')
                else:
                    logger.error(f"File {predicted_img_path_str} does not exist. Cannot upload to S3.")
                    continue
            except Exception as e:
                logger.error(f'Failed to upload {predicted_img_path_str} to bucket {images_bucket}. Error: {e}')
                continue

            try:
                pred_summary_path = predicted_img_dir / f'labels/{img_name.split(".")[0]}.txt'
                logger.info(f'Prediction summary path: {pred_summary_path}')
                if pred_summary_path.exists():
                    with open(pred_summary_path) as f:
                        labels = f.read().splitlines()
                        labels = [line.split(' ') for line in labels]
                        labels = [{
                            'class': names[int(l[0])],
                            'cx': Decimal(l[1]),
                            'cy': Decimal(l[2]),
                            'width': Decimal(l[3]),
                            'height': Decimal(l[4]),
                        } for l in labels]

                    logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')
                    message_text = f"Prediction Summary for image {original_img_path}:\n\n"
                    for label in labels:
                        message_text += f"Class: {label['class']}\n"
                        message_text += f"CX: {label['cx']}\n"
                        message_text += f"CY: {label['cy']}\n"
                        message_text += f"Width: {label['width']}\n"
                        message_text += f"Height: {label['height']}\n\n"

                    prediction_summary = {
                        'prediction_id': prediction_id,
                        'original_img_path': original_img_path,
                        'predicted_img_path': predicted_img_path_str,
                        'labels': message_text,
                        'time': int(time.time()),
                        'chat_id': chat_id
                    }

                    new_item = table.put_item(Item=prediction_summary)
                    logger.info(f"Item added successfully to DynamoDB: {new_item}")

                get_request = requests.get(f"https://tamer.atech-bot.click/results?predictionId={prediction_id}", verify=False, timeout=10)
                logger.info(f"GET request to Polybot completed with status: {get_request.status_code}")

                sqs_client.delete_message(QueueUrl=queue_name, ReceiptHandle=receipt_handle)
                logger.info(f'Message {prediction_id} deleted from queue')
            except Exception as e:
                logger.error(f'Failed to complete post-processing for {prediction_id}. Error: {e}')
                continue

if __name__ == "__main__":
    logger.info("Starting Flask app for health checks...")

    # Start the SQS message consumption in a separate thread
    consumer_thread = threading.Thread(target=consume)
    consumer_thread.start()

    # Start the Flask app for health checks in the main thread
    app.run(host='0.0.0.0', port=80, debug=False)

    # Ensure the consumer thread shuts down gracefully
    consumer_thread.join()
