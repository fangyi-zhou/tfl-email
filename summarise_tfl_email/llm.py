import os

import vertexai
from vertexai.language_models import TextGenerationModel

PROJECT = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
PROMPT = """
Given a summary of disruptions and events happening this weekend using the \
provided weekend travel information.
For disruptions, include station names, line names, and dates.
Remember to include disruptions of all modes of transport: Tube, London
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


def produce_summary(content: str) -> str:
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
    response = model.predict(PROMPT % content, **parameters)
    # print(response.text)
    return response.text
