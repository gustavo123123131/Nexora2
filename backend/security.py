"""Access token and secure secret store."""
import secrets
from pathlib import Path

import keyring

class SecretStore:
    service = 'Nexora2Proxy'
    def put(self, key, value):
        keyring.set_password(self.service, key, value)
    def get(self, key):
        return keyring.get_password(self.service, key)
    def delete(self, key):
        try:
            keyring.delete_password(self.service, key)
        except keyring.errors.PasswordDeleteError:
            pass

def load_token(root: Path):
    file = root / '.local-token'
    if file.exists():
        return file.read_text().strip()
    value = secrets.token_urlsafe(48)
    try:
        with file.open('x') as f:
            f.write(value)
        file.chmod(0o600)
    except FileExistsError:
        return file.read_text().strip()
    return value
