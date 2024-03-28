import json

import boto3

PROMPT = """
Given a summary of disruptions and events happening this weekend using the \
provided weekend travel information.
For disruptions, include station names, line names, and dates.
Remember to include disruptions of all modes of transport: Tube, London \
Overground, DLR, Elizabeth Line, Trams and Trains.
For events, remove sentences about increased traffic or large crowds.

Weekend travel information: %s

Disruptions:
"""
LLAMA2_70B = "meta.llama2-70b-chat-v1"


def produce_summary(content: str) -> str:
    # eu-west-1 currently doesn't have Bedrock
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    text_input = PROMPT % content
    print(text_input)
    print("Invoking LLM...")
    response = client.invoke_model(
        body=json.dumps(
            {
                "prompt": text_input,
                "max_gen_len": 2048,
                "temperature": 0,
                "top_p": 0.2,
            }
        ),
        modelId=LLAMA2_70B,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    response_text = response_body["generation"]
    # print(response_text)
    return "Disruptions:" + response_text
