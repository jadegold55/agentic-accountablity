import json
from groq import Groq
import os
from typing import Any

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


def interpret_completion_reply(text: str, event_title: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=os.getenv("INFERENCE_LLM_MODEL", "llama-3.1-8b-instant"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You interpret whether a user's reply describes how much of an "
                    "event or task they completed. Respond with valid JSON only. "
                    "Use intent values log_completion, clarify_completion, or "
                    "not_completion. For log_completion, include rating as an integer "
                    "from 0 to 5, confidence as high/medium/low, a short "
                    "completion_summary, and an acknowledgment message to send back. "
                    "For clarify_completion, set rating to null, include a short "
                    "clarifying_question, and confidence low or medium. For "
                    "not_completion, set rating to null and leave the other text "
                    "fields empty. Treat clear completion language like 'did half', "
                    "'finished it', 'barely started', or 'got most of it done' as "
                    "completion updates."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Event title: {event_title}\n"
                    f"User reply: {text}\n"
                    "Return JSON with keys: intent, rating, confidence, "
                    "completion_summary, clarifying_question, acknowledgment."
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    message = response.choices[0].message.content.strip()
    return json.loads(message)


def generate_scheduled_message(
    workflow_type: str, event_title: str, scheduled_for: str
) -> str:
    response = client.chat.completions.create(
        model=os.getenv("SCHEDULED_MESSAGE_LLM_MODEL", "llama-3.1-8b-instant"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Write one short Telegram message for an accountability bot. "
                    "If workflow_type is checkin, write a reminder that the event is "
                    "starting or happening now. Do not ask for a rating. If "
                    "workflow_type is nudge, write a short follow-up asking how the "
                    "event went. Sound human and casual. Return plain text only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"workflow_type: {workflow_type}\n"
                    f"event_title: {event_title}\n"
                    f"scheduled_for: {scheduled_for}"
                ),
            },
        ],
    )
    return response.choices[0].message.content.strip()


def generate_weekly_summary(prompt: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("SUMMARY_LLM_MODEL", "llama-3.1-8b-instant"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You write a brief weekly accountability summary for a human. "
                    "Be honest, grounded in the provided stats, and encouraging "
                    "without sounding corporate or overhyped. Return plain text only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()
