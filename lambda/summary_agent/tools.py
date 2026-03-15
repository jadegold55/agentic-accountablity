import os
from pathlib import Path
from datetime import datetime
from shared.telegram import (
    send_message as telegram_send_message,
    send_photo as telegram_send_photo,
)


def _get_pyplot():
    import matplotlib

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def generate_bar_chart(labels: list[str], values: list[float], title: str):
    """
    Generates a bar chart from the given data.
    The chart is saved as a PNG file in the /tmp directory with a unique name
    based on the title and then sent via the `send_photo` function to telegram.
    """
    filename = f"/tmp/bar_{title}.png"
    plt = _get_pyplot()

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
    plt = _get_pyplot()

    plt.figure()
    plt.imshow(ratings, cmap="hot", interpolation="nearest")
    plt.xticks(range(len(days)), labels=days)
    plt.yticks(range(len(tasks)), labels=tasks)
    plt.colorbar(label="Rating")
    plt.title(title)
    plt.savefig(filename)
    plt.close()

    return filename


def send_photo(photo_path: str, caption: str | None = None):
    """
    Sends a photo via Telegram.
    """
    telegram_send_photo(photo_path, caption)
    return photo_path


def send_message(text: str):
    """
    Sends a message via Telegram.
    """

    telegram_send_message(text)


def build_heat_map_inputs(checkin_items):
    rated_items = [item for item in checkin_items if item.get("rating") is not None]
    if not rated_items:
        return None

    tasks = sorted(
        {item.get("event_title", "") for item in rated_items if item.get("event_title")}
    )
    day_keys = sorted(
        {
            item.get("checkins", {}).get("sent_at", "")[:10]
            for item in rated_items
            if item.get("checkins", {}).get("sent_at")
        }
    )

    if len(tasks) < 2 or len(day_keys) < 2:
        return None

    day_labels = []
    day_index = {}
    for day_key in day_keys:
        label = datetime.fromisoformat(day_key).strftime("%a")
        day_index[day_key] = len(day_labels)
        day_labels.append(label)

    task_index = {task: index for index, task in enumerate(tasks)}
    ratings_grid = [[0.0 for _ in day_labels] for _ in tasks]
    counts_grid = [[0 for _ in day_labels] for _ in tasks]

    for item in rated_items:
        task = item.get("event_title")
        sent_at = item.get("checkins", {}).get("sent_at")
        day_key = sent_at[:10] if sent_at else ""
        if task not in task_index or day_key not in day_index:
            continue
        row = task_index[task]
        col = day_index[day_key]
        ratings_grid[row][col] += float(item["rating"])
        counts_grid[row][col] += 1

    for row_index, row in enumerate(ratings_grid):
        for col_index, value in enumerate(row):
            count = counts_grid[row_index][col_index]
            if count:
                ratings_grid[row_index][col_index] = value / count

    return {
        "tasks": tasks,
        "days": day_labels,
        "ratings": ratings_grid,
    }
