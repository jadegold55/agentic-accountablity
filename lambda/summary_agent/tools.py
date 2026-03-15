from operator import add
from os import link
from turtle import st
import matplotlib.pyplot as plt
from langchain_core.tools import tool
from shared.telegram import (
    send_message as telegram_send_message,
    send_photo as telegram_send_photo,
)


@tool
def generate_bar_chart(labels: list[str], values: list[float], title: str):
    """
    Generates a bar chart from the given data.
    The chart is saved as a PNG file in the /tmp directory with a unique name
    based on the title and then sent via the `send_photo` function to telegram.
    """
    filename = f"/tmp/bar_{title}.png"

    plt.figure()
    plt.bar(labels, values)
    plt.title(title)
    plt.savefig(filename)
    plt.close()

    return filename


def generate_heat_map(
    tasks: list[str], days: list[str], ratings: list[list[float]], title: str
):
    """
    Generates a heat map from the given data.
    Saves the heat map as a PNG file in the /tmp directory with a unique name based
    on the title and sends it via the `send_photo` function to telegram.



    """
    filename = f"/tmp/heatmap_{title}.png"

    plt.figure()
    plt.imshow(ratings, cmap="hot", interpolation="nearest")
    plt.xticks(range(len(days)), labels=days)
    plt.yticks(range(len(tasks)), labels=tasks)
    plt.colorbar(label="Rating")
    plt.title(title)
    plt.savefig(filename)
    plt.close()

    return filename


@tool
def send_photo(photo_path: str, caption: str | None = None):
    """
    Sends a photo via Telegram.
    """
    telegram_send_photo(photo_path, caption)


@tool
def send_message(text: str):
    """
    Sends a message via Telegram.
    """

    telegram_send_message(text)


summarytools = [generate_bar_chart, generate_heat_map, send_photo, send_message]
