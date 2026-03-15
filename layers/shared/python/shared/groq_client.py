from groq import Groq
import os

from .config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)


def classify_message(text: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("CLASSIFIER_LLM_MODEL", "llama-3.1-8b-instant"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the following message as either a command or a "
                    "question. Respond with only one word."
                ),
            },
            {"role": "user", "content": f"{text}"},
        ],
    )
    classification = response.choices[0].message.content.strip().lower()
    return classification
