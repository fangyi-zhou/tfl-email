import asyncio
import datetime
import json
import os

import boto3

SUMMARY_TABLE_NAME = os.environ.get("SUMMARY_TABLE_NAME")
FALLBACK_MESSAGE = """No summary availble for this week, try again later \
(usually after Thursday noon)."""
REGION_NAME = "eu-west-1"
SECRET_NAME = os.environ.get("TELEGRAM_SECRET_NAME")


def load_summary_by_key(key: str) -> str:
    dynamodb = boto3.resource("dynamodb")
    key = {
        "week-id": key,
    }
    attributes_to_get = ["summary"]
    table = dynamodb.Table(SUMMARY_TABLE_NAME)
    resp = table.get_item(Key=key, AttributesToGet=attributes_to_get)
    # print(f"Got response from DynamoDB: {resp}")
    return resp["Item"]["summary"] if "Item" in resp else FALLBACK_MESSAGE


def load_summary() -> str:
    now = datetime.datetime.now()
    week_number = now.strftime("%Y-%W")
    return load_summary_by_key(week_number)


def load_telegram_credentials():
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
    telegram_credentials = get_secret_value_response["SecretString"]
    return json.loads(telegram_credentials)


def handle_telegram_webhook(event):
    import telegram

    credentials = load_telegram_credentials()
    print("Loaded telegram credentials")
    if (
        event["headers"].get("x-telegram-bot-api-secret-token")
        != credentials["webhook_validation_token"]
    ):
        print("Ignoring possibly spoofed request")
        return {"statusCode": 403}
    body = json.loads(event["body"])
    bot = telegram.Bot(token=credentials["bot_token"])
    update = telegram.Update.de_json(body, bot)
    if (
        update.message is not None
        and update.message.text is not None
        and update.message.text.startswith("/info")
    ):
        summary = load_summary()
        asyncio.run(update.message.reply_text(summary[:4096]))
    return {"statusCode": 200}


def lambda_handler(event, context):
    if event["rawPath"] == "/telegram-webhook":
        return handle_telegram_webhook(event)
    return {"statusCode": 200, "body": load_summary()}
