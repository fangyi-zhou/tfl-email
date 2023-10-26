import email
import json
import os

import boto3
import requests

import llm

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
SECRET_NAME = os.environ.get("GCP_SECRET_NAME")
REGION_NAME = "eu-west-1"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_API_ENDPOINT = (
    "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
)


def load_gcp_credentials():
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
    gcp_cred = get_secret_value_response["SecretString"]
    with open("/tmp/credentials.json", "w") as f:
        f.write(gcp_cred)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"


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
    texts = [
        part.get_payload()
        for part in msg.walk()
        if part.get_content_type() == "text/plain"
    ]
    summary = llm.produce_summary("\n".join(texts))
    print(f"Got summary from LLM: {summary}")

    r = requests.post(
        TELEGRAM_API_ENDPOINT,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": summary,
            "parse_mode": "Markdown",
        },
    )
    print(f"Got response from Telegram {r.json()}")

    return {
        "statusCode": 200,
    }
