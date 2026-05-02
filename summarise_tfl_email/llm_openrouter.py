import json
import os

import boto3
import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "moonshotai/kimi-k2.6"
REGION_NAME = "eu-west-1"

SYSTEM_PROMPT = (
    "You are a travel information assistant. "
    "Give a concise summary of disruptions and events from the provided TfL weekend travel information. "
    "Format the output for Telegram: use **bold** for section names and line names, and • bullet characters for list items. "
    "Do not use Markdown headers (#), dashes for bullets (-), or tables. "
    "For disruptions, group by transport mode. Each disruption should be a • bullet including: line/service name in bold, affected stations, and dates. "
    "Include all modes of transport: Tube, London Overground, DLR, Elizabeth Line, Trams, IFS Cloud Cable Car, and National Rail. "
    "Only include modes that have disruptions. "
    "For events, list each as a • bullet with venue, event type, and time. Omit any commentary about crowds or traffic."
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
