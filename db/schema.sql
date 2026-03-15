    CREATE TABLE tasks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        type TEXT CHECK (type IN ('habit', 'task', 'goal')),
        frequency TEXT,
        deadline TIMESTAMPTZ,
        active BOOLEAN DEFAULT true
    );

    CREATE TABLE checkins(
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        calendar_event_id TEXT,
        
        sent_at TIMESTAMPTZ DEFAULT now(),
        
        status TEXT CHECK (status IN ('sent', 'responded', 'nudged', 'missed')) NOT NULL
    );

    CREATE TABLE checkin_items(
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        checkin_id UUID REFERENCES checkins(id),
        task_id UUID REFERENCES tasks(id),
        event_title TEXT,
        raw_reply_text TEXT,
        completion_summary TEXT,
        rating SMALLINT CHECK (rating >= 0 AND rating <= 5) -- null until responded
    );

CREATE TABLE weekly_summaries(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start_date TIMESTAMPTZ NOT NULL,
    completion_json JSONB,
    summary TEXT,
    sent_at TIMESTAMPTZ DEFAULT now()
);