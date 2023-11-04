import datetime
import json
import os

import boto3

SUMMARY_TABLE_NAME = os.environ.get("SUMMARY_TABLE_NAME")
FALLBACK_MESSAGE = """No summary availble for this week, try again later \
(usually after Thursday noon)."""


def load_summary(key: str) -> str:
    dynamodb = boto3.resource("dynamodb")
    key = {
        "week-id": key,
    }
    attributes_to_get = ["summary"]
    table = dynamodb.Table(SUMMARY_TABLE_NAME)
    resp = table.get_item(Key=key, AttributesToGet=attributes_to_get)
    print(f"Got response from DynamoDB: {resp}")
    return resp["Item"]["summary"] if "Item" in resp else FALLBACK_MESSAGE


def lambda_handler(event, context):
    now = datetime.datetime.now()
    week_number = now.strftime("%Y-%W")
    summary = load_summary(week_number)

    return {"statusCode": 200, "body": summary}
