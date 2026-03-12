from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_active_tasks():
    response = supabase.table("tasks").select("*").eq("active", True).execute()

    return response.data


def add_task(task):
    response = supabase.table("tasks").insert(task).execute()

    return response.data


def update_task(task_id, updates):
    response = supabase.table("tasks").update(updates).eq("id", task_id).execute()

    return response.data


def delete_task(task_id):
    response = supabase.table("tasks").delete().eq("id", task_id).execute()

    return response.data


def add_check_in(check_in):
    response = supabase.table("checkins").insert(check_in).execute()
    add
    return response.data


def get_check_ins():
    response = supabase.table("checkins").select("*").execute()

    return response.data


def update_checkin_status(checkin_id, status):
    response = (
        supabase.table("checkins")
        .update({"status": status})
        .eq("id", checkin_id)
        .execute()
    )
    return response.data


def update_checkin_item_rating(checkin_item_id, rating):
    response = (
        supabase.table("checkin_items")
        .update({"rating": rating})
        .eq("id", checkin_item_id)
        .execute()
    )
    return response.data


def get_checkin_items_by_date_range(start_date, end_date):
    response = (
        supabase.table("checkin_items")
        .select("*, checkins(*), tasks(*)")
        .gte("checkins.sent_at", start_date)
        .lte("checkins.sent_at", end_date)
        .execute()
    )
    return response.data


def add_checkin_item(checkin_item):
    response = supabase.table("checkin_items").insert(checkin_item).execute()
    return response.data
