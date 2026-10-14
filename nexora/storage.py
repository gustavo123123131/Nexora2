"""SQLite persistence and encrypted-on-disk proxy credentials."""
import os
import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone
from cryptography.fernet import Fernet


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Store:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.profiles_dir = self.root / 'browser-profiles'
        self.profiles_dir.mkdir(exist_ok=True)
        key_path = self.root / 'secrets.key'
        if not key_path.exists():
            fd = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(Fernet.generate_key())
        self.cipher = Fernet(key_path.read_bytes())
        self.db_path = self.root / 'nexora.db'
        self._init_db()

    def db(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA journal_mode=WAL')
        return db

    def _init_db(self):
        with self.db() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS proxies (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, scheme TEXT NOT NULL,
                host TEXT NOT NULL, port INTEGER NOT NULL,
                username TEXT NOT NULL DEFAULT '', password_enc TEXT NOT NULL DEFAULT '',
                last_status TEXT NOT NULL DEFAULT 'unchecked', last_ip TEXT,
                last_error TEXT, checked_at TEXT, created_at TEXT NOT NULL
              );
              CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, device_id TEXT NOT NULL,
                width INTEGER NOT NULL, height INTEGER NOT NULL,
                locale TEXT NOT NULL DEFAULT 'pt-BR', timezone TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
                tags TEXT NOT NULL DEFAULT '[]', group_name TEXT NOT NULL DEFAULT '',
                proxy_id TEXT REFERENCES proxies(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
              );
              CREATE TABLE IF NOT EXISTS custom_devices (
                id TEXT PRIMARY KEY, label TEXT NOT NULL,
                base_id TEXT NOT NULL, width INTEGER NOT NULL,
                height INTEGER NOT NULL, created_at TEXT NOT NULL
              );
              CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                level TEXT NOT NULL, category TEXT NOT NULL, message TEXT NOT NULL
              );
            ''')
            db.execute("INSERT OR IGNORE INTO settings VALUES ('max_running', '3')")
            db.execute("INSERT OR IGNORE INTO settings VALUES ('warn_shared_proxy', 'true')")
            db.execute("INSERT OR IGNORE INTO settings VALUES ('min_free_mb', '512')")

    def settings(self):
        with self.db() as db:
            return {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM settings')}

    def set_settings(self, opts):
        with self.db() as db:
            for key, value in opts.items():
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, json.dumps(value)))
        return self.settings()

    def log(self, level, category, message):
        # Caller passes only fixed/sanitized error messages; never credentials.
        with self.db() as db:
            db.execute('INSERT INTO logs(at,level,category,message) VALUES (?,?,?,?)',
                       (now(), level, category, str(message)[:500]))
            db.execute('DELETE FROM logs WHERE id NOT IN (SELECT id FROM logs ORDER BY id DESC LIMIT 500)')

    def logs(self, limit=100):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM logs ORDER BY id DESC LIMIT ?', (limit,))]

    def list_custom_devices(self):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM custom_devices ORDER BY label')]

    def get_custom_device(self, device_id):
        with self.db() as db:
            row = db.execute('SELECT * FROM custom_devices WHERE id=?', (device_id,)).fetchone()
        return dict(row) if row else None

    def create_custom_device(self, label, base_id, width, height):
        device_id = 'custom-' + str(uuid.uuid4())
        with self.db() as db:
            db.execute('INSERT INTO custom_devices(id,label,base_id,width,height,created_at) VALUES (?,?,?,?,?,?)',
                       (device_id,label,base_id,width,height,now()))
        return self.get_custom_device(device_id)

    def delete_custom_device(self, device_id):
        with self.db() as db:
            if db.execute('SELECT 1 FROM profiles WHERE device_id=?', (device_id,)).fetchone():
                raise ValueError('Dispositivo está sendo utilizado em um perfil')
            cur = db.execute('DELETE FROM custom_devices WHERE id=?', (device_id,))
        return bool(cur.rowcount)

    def list_profiles(self):
        with self.db() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM profiles ORDER BY updated_at DESC')]
        for r in rows:
            r['tags'] = json.loads(r['tags'])
        return rows

    def get_profile(self, profile_id):
        with self.db() as db:
            row = db.execute('SELECT * FROM profiles WHERE id=?', (profile_id,)).fetchone()
        if not row:
            return None
        obj = dict(row)
        obj['tags'] = json.loads(obj['tags'])
        return obj

    def save_profile(self, data, profile_id=None):
        ts = now()
        with self.db() as db:
            if profile_id:
                if not db.execute('SELECT 1 FROM profiles WHERE id=?', (profile_id,)).fetchone():
                    return None
                db.execute('''UPDATE profiles SET name=?, device_id=?, width=?, height=?, locale=?,
                 timezone=?, tags=?, group_name=?, proxy_id=?, updated_at=? WHERE id=?''',
                 (data['name'], data['device_id'], data['width'], data['height'],
                  data['locale'], data['timezone'], json.dumps(data['tags']), data['group_name'],
                  data.get('proxy_id'), ts, profile_id))
                result_id = profile_id
            else:
                result_id = str(uuid.uuid4())
                db.execute('''INSERT INTO profiles
                (id,name,device_id,width,height,locale,timezone,tags,group_name,proxy_id,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                (result_id, data['name'], data['device_id'], data['width'], data['height'],
                 data['locale'], data['timezone'], json.dumps(data['tags']), data['group_name'],
                 data.get('proxy_id'), ts, ts))
        return self.get_profile(result_id)

    def delete_profile(self, profile_id):
        with self.db() as db:
            cur = db.execute('DELETE FROM profiles WHERE id=?', (profile_id,))
        return bool(cur.rowcount)

    def list_proxies(self):
        with self.db() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM proxies ORDER BY created_at DESC')]
        for p in rows:
            p['has_password'] = bool(p.pop('password_enc'))
        return rows

    def get_proxy(self, proxy_id, reveal=False):
        with self.db() as db:
            row = db.execute('SELECT * FROM proxies WHERE id=?', (proxy_id,)).fetchone()
        if not row:
            return None
        p = dict(row)
        p['has_password'] = bool(p['password_enc'])
        if reveal:
            p['password'] = self.cipher.decrypt(p['password_enc'].encode()).decode() if p['password_enc'] else ''
        del p['password_enc']
        return p

    def save_proxy(self, data, proxy_id=None):
        if proxy_id:
            old = self.get_proxy(proxy_id, reveal=True)
            if not old:
                return None
            password = old['password'] if data.get('password') is None else data['password']
        else:
            password = data.get('password') or ''
        secret = self.cipher.encrypt(password.encode()).decode() if password else ''
        with self.db() as db:
            if proxy_id:
                db.execute('''UPDATE proxies SET name=?,scheme=?,host=?,port=?,username=?,password_enc=?,
                  last_status='unchecked',last_ip=NULL,last_error=NULL,checked_at=NULL WHERE id=?''',
                  (data['name'], data['scheme'], data['host'], data['port'], data.get('username') or '', secret, proxy_id))
                result_id = proxy_id
            else:
                result_id = str(uuid.uuid4())
                db.execute('''INSERT INTO proxies
                  (id,name,scheme,host,port,username,password_enc,created_at)
                  VALUES(?,?,?,?,?,?,?,?)''',
                  (result_id, data['name'], data['scheme'], data['host'], data['port'],
                   data.get('username') or '', secret, now()))
        return self.get_proxy(result_id)

    def set_proxy_test(self, proxy_id, status, ip='', error=''):
        with self.db() as db:
            db.execute('UPDATE proxies SET last_status=?, last_ip=?,last_error=?,checked_at=? WHERE id=?',
                       (status, ip or None, error or None, now(), proxy_id))

    def delete_proxy(self, proxy_id):
        with self.db() as db:
            cur = db.execute('DELETE FROM proxies WHERE id=?', (proxy_id,))
        return bool(cur.rowcount)
