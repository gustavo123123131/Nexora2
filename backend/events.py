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
