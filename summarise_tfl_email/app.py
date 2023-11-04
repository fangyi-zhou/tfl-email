import datetime
import email
import email.utils
import json
import os
import re

import boto3
import requests
from bs4 import BeautifulSoup

import llm

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
SECRET_NAME = os.environ.get("GCP_SECRET_NAME")
REGION_NAME = "eu-west-1"
SUMMARY_TABLE_NAME = os.environ.get("SUMMARY_TABLE_NAME")


def load_gcp_credentials():
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
    gcp_cred = get_secret_value_response["SecretString"]
    with open("/tmp/credentials.json", "w") as f:
        f.write(gcp_cred)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"


def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(" ")
    return re.sub("\s+", " ", text).strip()


def lambda_handler(event, context):
    load_gcp_credentials()
    print("Loaded GCP Credentials successfully")

    s3 = boto3.resource("s3")
    message_id = event["Records"][0]["ses"]["mail"]["messageId"]
    email_object = s3.Object(
        bucket_name=S3_BUCKET_NAME,
        key=message_id,
    )
    resp = email_object.get()
    data = resp["Body"].read()
    print(f"Loaded email message ID {message_id}")

    msg = email.message_from_bytes(data)
    if msg["Subject"] != "Weekend travel advice":
        print(f'Skipping email with subject {msg["Subject"]}')
        return {
            "statusCode": 200,
        }

    texts = [
        part.get_payload()
        for part in msg.walk()
        if part.get_content_type() == "text/html"
    ]
    content = clean_html("\n".join(texts))
    summary = llm.produce_summary(content)
    print(f"Got summary from LLM: {summary}")

    email_date = email.utils.parsedate_to_datetime(msg.get("Date"))
    week_number = email_date.strftime("%Y-%W")
    print(f"Email is dated {email_date}, converting to {week_number}")
    ttl = email_date + datetime.timedelta(days=15)
    item = {
        "week-id": {"S": week_number},
        "summary": {"S": summary},
        "ttl": {"N": str(int(ttl.timestamp()))},
        "email-id": {"S": message_id},
    }
    dynamodb = boto3.client("dynamodb")
    resp = dynamodb.put_item(TableName=SUMMARY_TABLE_NAME, Item=item)
    print(f"Got response from DynamoDB: {resp}")

    return {
        "statusCode": 200,
    }
