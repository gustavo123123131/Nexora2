"""Local-only configuration."""
import os
from pathlib import Path

def storage_dir() -> Path:
    value = os.getenv("NEXORA_HOME")
    return Path(value).expanduser().resolve() if value else (Path.home() / ".nexora2").resolve()

def port() -> int:
    value = int(os.getenv("NEXORA_PORT", "8765"))
    if not 0 <= value <= 65535:
        raise ValueError("NEXORA_PORT outside valid range")
    return value

def ip_check_url() -> str:
    return os.getenv("NEXORA_IP_CHECK_URL", "https://api.ipify.org?format=json")
