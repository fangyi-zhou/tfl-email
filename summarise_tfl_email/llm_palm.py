import os

import boto3
import vertexai
from vertexai.language_models import TextGenerationModel

GCP_SECRET_NAME = os.environ.get("GCP_SECRET_NAME")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
PROJECT = os.environ.get("GCP_PROJECT")
PROMPT = """
Given a summary of disruptions and events happening this weekend using the \
provided weekend travel information.
For disruptions, include station names, line names, and dates.
Remember to include disruptions of all modes of transport: Tube, London \
Overground, DLR, Elizabeth Line, Trams and Trains.
For events, remove sentences about increased traffic or large crowds.

Weekend travel information: %s

Disruptions:
*
*
*

Events:
*
*
*
"""


def load_gcp_credentials():
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")
    get_secret_value_response = client.get_secret_value(SecretId=GCP_SECRET_NAME)
    gcp_cred = get_secret_value_response["SecretString"]
    with open("/tmp/credentials.json", "w") as f:
        f.write(gcp_cred)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"


def produce_summary(content: str) -> str:
    load_gcp_credentials()
    print("Loaded GCP Credentials successfully")

    vertexai.init(project=PROJECT, location=LOCATION)
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 1024,
        "temperature": 0.05,
        "top_p": 0.15,
        "top_k": 20,
    }
    model = TextGenerationModel.from_pretrained("text-bison")
    text_input = PROMPT % content
    print(text_input)
    print("Invoking LLM...")
    response = model.predict(PROMPT % content, **parameters)
    # print(response.text)
    return response.text
