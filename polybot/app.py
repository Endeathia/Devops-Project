import flask
from flask import request
import os
from bot import ObjectDetectionBot
import boto3
import json
import sys
import signal
from threading import Thread
import requests

app = flask.Flask(__name__)


# TODO load TELEGRAM_TOKEN value from Secret Manager



secrets_manager_client = boto3.client('secretsmanager', region_name='us-west-1')
secret_name = 'TELEGRAM_TOKEN_NEW'
response = secrets_manager_client.get_secret_value(SecretId=secret_name)
secret_string = response['SecretString']
secret_dict = json.loads(secret_string)
TELEGRAM_TOKEN = secret_dict['TELEGRAM_TOKEN']
telegram_chat_url = os.environ['telegram_chat_url']

def handle_sigterm(*args):
    print("Received SIGTERM. Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

@app.route('/health')
def health_check():
    if all_required_services_are_running():
        return 'OK', 200
    else:
        return 'Service Unavailable', 500

def all_required_services_are_running():
    return True

@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


@app.route(f'/results/', methods=['GET', 'POST'])
def results():
    prediction_id = request.args.get('predictionId')

    # TODO use the prediction_id to retrieve results from DynamoDB and send to the end-user
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table_name = 'Yolo-Project'
    table = dynamodb.Table(table_name)
    response = table.get_item(
        Key={
            'prediction_id': prediction_id
        }
    )
    item = response.get('Item')


    chat_id = item.get('chat_id')
    text_results = item.get('labels')

    bot.send_text(chat_id, text_results)
    return 'Ok'


@app.route(f'/loadTest/', methods=['POST'])
def load_test():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'

def run_flask():
    app.run(host='0.0.0.0')



if __name__ == "__main__":
    bot = ObjectDetectionBot(TELEGRAM_TOKEN, telegram_chat_url)
    app.run(host='0.0.0.0', port=8443, debug=True)


response = requests.get('http://127.0.0.1:8443/health')
print(response.status_code)
print(response.text)