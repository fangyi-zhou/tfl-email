import os

import vertexai
from vertexai.language_models import TextGenerationModel

PROJECT = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
PROMPT = """
Use the provided weekend travel information. \
Please provide a summary of disruptions and events happening this weekend.

When describing disruptions, please include station names, line names, and \
dates, for example:
On [DATE], no service on [LINE] between [STATION] and [STATION].

When describing events, please REMOVE "Large crowds are expected" or "Increased traffic is expected".

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
        "temperature": 0.1,
        "top_p": 0.25,
        "top_k": 30,
    }
    model = TextGenerationModel.from_pretrained("text-bison")
    text_input = PROMPT % content
    print(text_input)
    response = model.predict(PROMPT % content, **parameters)
    # print(response.text)
    return response.text
