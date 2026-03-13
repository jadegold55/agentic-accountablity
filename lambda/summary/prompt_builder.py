def build_summary_prompt(stats):
    prompt = "The scale is from 0 to 5, where 0 is uncompleted and 5 is completed. Anything between those are incremental increases in completion but not fully completed. Here is the summary of the week's check-ins:\n\n"
    prompt += "Average rating per task:\n"
    for task, rating in stats["per_task"].items():
        prompt += f"- {task}: {rating:.2f}\n"
    prompt += "\nAverage rating per day:\n"
    for day, rating in stats["per_day"].items():
        prompt += f"- {day}: {rating:.2f}\n"
    return (
        prompt
        + "\nGive a brief summary of the week's performance based on the above statistics, be honest but encouraging. "
    )
