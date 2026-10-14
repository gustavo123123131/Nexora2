"""Record local diagnostic events."""
import json
from datetime import datetime, timezone


def record(app, action, uid):
    item = {'time': datetime.now(timezone.utc).isoformat(), 'action': action, 'profile_id': uid}
    app.state.events.append(item)
    try:
        with (app.state.db.root / 'events.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(item) + '\n')
    except OSError:
        pass


def recent(app):
    from collections import deque
    path = app.state.db.root / 'events.jsonl'
    if not path.exists():
        return list(reversed(app.state.events[-300:]))
    try:
        with path.open(encoding='utf-8') as stream:
            records = deque(stream, maxlen=300)
        return [json.loads(line) for line in reversed(records) if line.strip()]
    except (OSError, ValueError):
        return list(reversed(app.state.events[-300:]))
