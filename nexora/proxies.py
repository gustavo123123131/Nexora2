"""Proxy parsing, validation and safe Playwright options."""
import ipaddress
import re
from urllib.parse import urlsplit

HOST_PATTERN = re.compile(r'^(?=.{1,253}$)[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*$')
ALLOWED_SCHEMES = {'http', 'socks5'}


def validate_proxy(scheme, host, port):
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError('Tipo de proxy: use HTTP ou SOCKS5 (HTTPS via CONNECT em proxy HTTP)')
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ValueError('Porta inválida (1–65535)')
    if not isinstance(host, str) or not host or not (HOST_PATTERN.fullmatch(host) or _is_ip(host)):
        raise ValueError('Host de proxy inválido')


def _is_ip(host):
    try:
        ipaddress.ip_address(host.strip('[]'))
        return True
    except ValueError:
        return False


def parse_line(line):
    """Accept host:port[:user:password], scheme://host:port, IPv6 [addr]:port."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    scheme = 'http'
    if '://' in line:
        u = urlsplit(line)
        if not u.hostname or not u.port:
            raise ValueError('Formato de URL inválido')
        scheme = u.scheme.lower()
        host, port = u.hostname, u.port
        from urllib.parse import unquote
        username, password = unquote(u.username or ''), unquote(u.password or '')
    elif line.startswith('['):
        m = re.fullmatch(r'\[([^]]+)\]:(\d+)(?::([^:]*):(.*))?', line)
        if not m:
            raise ValueError('Formato IPv6 inválido')
        host, port, username, password = m.group(1), int(m.group(2)), m.group(3) or '', m.group(4) or ''
    else:
        parts = line.split(':', 3)
        if len(parts) not in (2, 4):
            raise ValueError('Use host:porta ou host:porta:usuario:senha')
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            raise ValueError('Porta inválida') from None
        username, password = (parts[2], parts[3]) if len(parts) == 4 else ('', '')
    validate_proxy(scheme, host, port)
    return {'name': f'{host}:{port}', 'scheme': scheme, 'host': host, 'port': port,
            'username': username, 'password': password}


def playwright_options(proxy):
    host = proxy['host']
    if ':' in host and not host.startswith('['):
        host = f'[{host}]'
    d = {'server': f"{proxy['scheme']}://{host}:{proxy['port']}"}
    if proxy.get('username'):
        d['username'] = proxy['username']
        d['password'] = proxy.get('password') or ''
    return d


def safe_error(exc):
    # Never propagate exception strings: driver errors can contain credentials/URLs.
    name = type(exc).__name__
    return f'Falha de conexão/inicialização ({name}). Verifique servidor, autenticação e rede.'
