from curses.ascii import isdigit
from shared.groq_client import classify_message


def classify_intent(message: str) -> str:
    """
    Classifies the intent of a given message.
    """

    ratings = message.split(" ")
    for a in ratings:
        if not a.isdigit() or int(a) > 5:
            return classify_message(message)

    return "rating"
