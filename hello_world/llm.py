import os

import vertexai
from vertexai.language_models import TextGenerationModel

PROJECT = os.environ.get("PROJECT")
LOCATION = os.environ.get("LOCATION", "us-central1")
PROMPT = """Here is the weekend travel information from Transport for London. \
Please provide a summary containing the information about weekend travel \
disruptions, and events that are happening this weekend."""

def produce_summary(content: str) -> str:
    vertexai.init(project=PROJECT, location=LOCATION)
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 1024,
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
    }
    model = TextGenerationModel.from_pretrained("text-bison")
    response = model.predict(
        PROMPT + "\n" + content,
        **parameters
    )
    # print(response.text)
    return response.text
