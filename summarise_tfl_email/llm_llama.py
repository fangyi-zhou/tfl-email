import json

from botocore.client import Config
import boto3

PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Given a summary of disruptions and events happening this weekend using the \
provided weekend travel information.
For disruptions, include station names, line names, and dates.
Remember to include disruptions of all modes of transport: Tube, London \
Overground, DLR, Elizabeth Line, Trams and Trains.
For events, remove sentences about increased traffic or large crowds.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Weekend travel information: %s<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
Disruptions:
"""
LLAMA2_70B = "meta.llama2-70b-chat-v1"
LLAMA31_70B = "meta.llama3-1-70b-instruct-v1:0"


def produce_summary(content: str) -> str:
    # Increase read timeout from 60 since LLM might take some time
    config = Config(
        read_timeout=180,
        # due to llama 3.1 is availability
        region_name="us-west-2",
        retries={
            "mode": "standard",
            "max_attempts": 5,
        },
    )
    client = boto3.client("bedrock-runtime", config=config)
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
        modelId=LLAMA31_70B,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    response_text = response_body["generation"]
    # print(response_text)
    return "Disruptions:\n" + response_text
