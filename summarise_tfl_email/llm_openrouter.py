import json
import os

import boto3
import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "minimax/minimax-m2.5"
REGION_NAME = "eu-west-1"

SYSTEM_PROMPT = (
    "Given a summary of disruptions and events happening this weekend using the "
    "provided weekend travel information. "
    "For disruptions, include station names, line names, and dates. "
    "Remember to include disruptions of all modes of transport: Tube, London "
    "Overground, DLR, Elizabeth Line, Trams and Trains. "
    "For events, remove sentences about increased traffic or large crowds."
)


def _get_api_key() -> str:
    secret_name = os.environ["OPENROUTER_SECRET_NAME"]
    client = boto3.client("secretsmanager", region_name=REGION_NAME)
    resp = client.get_secret_value(SecretId=secret_name)
    return json.loads(resp["SecretString"])["api_key"]


def produce_summary(content: str) -> str:
    api_key = _get_api_key()
    print("Invoking LLM via OpenRouter...")
    resp = requests.post(
        OPENROUTER_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Weekend travel information: {content}"},
            ],
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
