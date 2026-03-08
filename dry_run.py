#!/usr/bin/env python3
"""Dry-run the summariser Lambda with a recent email from S3."""

import base64
import json
import sys

import boto3

BUCKET = "tfl-fangyi-io-emails"
FUNCTION = "tfl-email-SummariseTflEmailFunction-hflZF2GTqCml"
REGION = "eu-west-1"


def get_latest_message_id():
    s3 = boto3.client("s3", region_name=REGION)
    resp = s3.list_objects_v2(Bucket=BUCKET)
    objects = sorted(resp["Contents"], key=lambda o: o["LastModified"], reverse=True)
    return objects[0]["Key"]


def main():
    message_id = sys.argv[1] if len(sys.argv) > 1 else get_latest_message_id()
    print(f"Using message ID: {message_id}")

    payload = {
        "dry_run": True,
        "Records": [{"ses": {"mail": {"messageId": message_id}}}],
    }

    lambda_client = boto3.client("lambda", region_name=REGION)
    print("Invoking Lambda (dry run)...")
    resp = lambda_client.invoke(
        FunctionName=FUNCTION,
        Payload=json.dumps(payload),
        LogType="Tail",
    )

    logs = base64.b64decode(resp["LogResult"]).decode()
    print("\n--- Logs ---")
    print(logs)

    body = json.loads(resp["Payload"].read())
    print("--- Response ---")
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()
