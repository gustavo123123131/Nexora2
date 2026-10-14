"""Strict import parser; errors never contain the raw credential line."""
import ipaddress
import re
from urllib.parse import urlsplit, unquote, quote
from .schemas import Proxy


def validate_host(host):
    try:
        ipaddress.ip_address(host)
        return
    except ValueError:
        pass
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?", host):
        raise ValueError("Invalid proxy hostname")


def parse_line(line):
    value = line.strip()
    if "://" in value:
        url = urlsplit(value)
        if url.scheme not in ("http", "https", "socks5") or not url.hostname:
            raise ValueError("Unsupported proxy address")
        try:
            data = {"scheme": url.scheme, "host": url.hostname, "port": url.port,
                    "username": unquote(url.username) if url.username else None,
                    "password": unquote(url.password) if url.password else None}
        except ValueError as exc:
            raise ValueError("Invalid proxy port") from None
    else:
        parts = value.split(":", 3)
        if len(parts) not in (2, 4):
            raise ValueError("Expected host:port or host:port:user:password")
        data = {"scheme": "http", "host": parts[0], "port": parts[1],
                "username": parts[2] if len(parts) == 4 else None,
                "password": parts[3] if len(parts) == 4 else None}
    validate_host(data["host"])
    data["name"] = f'{data["host"]}:{data["port"]}'
    return Proxy.model_validate(data)


def proxy_uri(proxy, password=None):
    host = proxy["host"]
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    auth = ""
    if proxy.get("username"):
        auth = quote(proxy["username"], safe="") + ":" + quote(password or "", safe="") + "@"
    return f'{proxy["scheme"]}://{auth}{host}:{proxy["port"]}'
