def build_summary_prompt(stats):
    prompt = "The scale is from 0 to 5, where 0 is uncompleted and 5 is completed. Anything between those are incremental increases in completion but not fully completed. Here is the summary of the week's check-ins:\n\n"
    prompt += "Average rating per task:\n"
    for task, rating in stats["per_task"].items():
        prompt += f"- {task}: {rating:.2f}\n"
    prompt += "\nAverage rating per day:\n"
    for day, rating in stats["per_day"].items():
        prompt += f"- {day}: {rating:.2f}\n"
    completion_notes = stats.get("completion_notes") or []
    if completion_notes:
        prompt += "\nCompletion notes from replies:\n"
        for item in completion_notes[:5]:
            prompt += f"- {item['event_title']}: {item['completion_summary']}\n"
    return (
        prompt
        + "\nWrite a brief weekly summary for the human based on these results. "
        + "Be honest, specific, and encouraging without sounding robotic. "
        + "Do not mention internal tools, charts, or implementation details."
    )
