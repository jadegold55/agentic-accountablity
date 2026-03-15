alter table checkin_items
add column if not exists event_title text,
add column if not exists raw_reply_text text,
add column if not exists completion_summary text;