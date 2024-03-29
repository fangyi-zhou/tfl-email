import datetime
import email
import email.utils
import json
import os
import re

import boto3
import markdown
import requests
from bs4 import BeautifulSoup

# import llm_palm as llm
import llm_llama as llm

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
TELEGRAM_SECRET_NAME = os.environ.get("TELEGRAM_SECRET_NAME")
REGION_NAME = "eu-west-1"
SUMMARY_TABLE_NAME = os.environ.get("SUMMARY_TABLE_NAME")
TELEGRAM_API_ENDPOINT = "https://api.telegram.org/bot%s/sendMessage"
REMOVE_UNSUPPORTED_HTML = re.compile(r"<\/?(?!(b|strong|i|em))[a-z]*>")


def load_telegram_credentials():
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    get_secret_value_response = client.get_secret_value(SecretId=TELEGRAM_SECRET_NAME)
    telegram_credentials = get_secret_value_response["SecretString"]
    return json.loads(telegram_credentials)


def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(" ")
    return re.sub(r"\s+", " ", text).strip()


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    message_id = event["Records"][0]["ses"]["mail"]["messageId"]
    email_object = s3.Object(
        bucket_name=S3_BUCKET_NAME,
        key=message_id,
    )
    resp = email_object.get()
    data = resp["Body"].read()
    print(f"Loaded email message ID {message_id}")

    is_dry_run = event.get("dry_run", False)

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

    if is_dry_run:
        # Finish processing here if dry run
        # Without storing the summary or publishing to Telegram
        return

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

    summary_html = markdown.markdown(summary)
    # Remove unsupported HTML tags by Telegram
    summary_html = REMOVE_UNSUPPORTED_HTML.sub("", summary_html)
    print(f"Sending summary in HTML:\n{summary_html}")
    telegram_creds = load_telegram_credentials()
    r = requests.post(
        TELEGRAM_API_ENDPOINT % telegram_creds["bot_token"],
        data={
            "chat_id": telegram_creds["channel_id"],
            "text": summary_html[:4096],
            "parse_mode": "html",
        },
    )
    r_json = r.json()
    print(f"Got response from Telegram {r_json}")
    if not r_json["ok"]:
        raise RuntimeError("Failed to post summary to Telegram")

    return {"statusCode": 200}
