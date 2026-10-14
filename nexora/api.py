"""Loopback-only authenticated management API."""
import asyncio
import html
import os
import re
import secrets
import shutil
import ipaddress
import socket
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from .storage import Store
from .browser import BrowserManager
from .devices import PRESETS, catalog
from .proxies import validate_proxy, parse_line

UI = Path(__file__).resolve().parent.parent / 'ui'


class ProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    device_id: str
    width: int = Field(ge=200, le=3000)
    height: int = Field(ge=300, le=4000)
    locale: str = Field(default='pt-BR', pattern=r'^[a-zA-Z]{2,3}(-[a-zA-Z]{2,4})?$', max_length=12)
    timezone: str = Field(default='America/Sao_Paulo', min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    group_name: str = Field(default='', max_length=80)
    proxy_id: str | None = None
    allow_shared_proxy: bool = False

    @field_validator('tags')
    @classmethod
    def clean_tags(cls, tags):
        if any(len(t) > 30 for t in tags):
            raise ValueError('Etiqueta muito longa')
        return list(dict.fromkeys(t.strip() for t in tags if t.strip()))

    @field_validator('timezone')
    @classmethod
    def valid_tz(cls, value):
        from zoneinfo import ZoneInfo
        try:
            ZoneInfo(value)
        except Exception:
            raise ValueError('Fuso horário IANA inválido') from None
        return value


class DeviceInput(BaseModel):
    label: str = Field(min_length=2, max_length=80)
    base_id: str
    width: int = Field(ge=200, le=3000)
    height: int = Field(ge=300, le=4000)


class ProxyInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    scheme: str = 'http'
    host: str = Field(min_length=1, max_length=253)
    port: int
    username: str = Field(default='', max_length=200)
    password: str | None = Field(default=None, max_length=500)

    @field_validator('scheme')
    @classmethod
    def lowercase(cls, val):
        return val.lower()


class ProxyImport(BaseModel):
    content: str = Field(max_length=150000)


class SettingsInput(BaseModel):
    max_running: int = Field(ge=1, le=30)
    warn_shared_proxy: bool = True
    min_free_mb: int = Field(default=512, ge=128, le=16384)


def create_app(data_dir=None, headless=False):
    root = Path(data_dir or os.environ.get('NEXORA_DATA_DIR', Path.home() / '.nexora-mobile'))
    store = Store(root)
    manager = BrowserManager(store, headless=headless)
    token = secrets.token_urlsafe(40)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await asyncio.to_thread(manager.close)

    app = FastAPI(title='Nexora Mobile', docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.store, app.state.manager, app.state.token = store, manager, token

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        # Pydantic exceptions include `input` by default: it may contain passwords.
        # Reject without echoing any submitted body, query or credentials.
        return JSONResponse(status_code=422, content={'detail': 'Dados inválidos: confira os campos e formatos.'})

    @app.middleware('http')
    async def secure_host(request: Request, call_next):
        # The server is additionally bound to 127.0.0.1 in __main__.
        host = request.headers.get('host', '').split(':')[0].strip('[]')
        if host not in ('localhost', '127.0.0.1', 'testserver'):
            return HTMLResponse('Invalid host', status_code=403)
        origin = request.headers.get('origin')
        if origin:
            from urllib.parse import urlsplit
            parsed = urlsplit(origin)
            if parsed.hostname not in ('localhost', '127.0.0.1') or parsed.scheme != 'http':
                return HTMLResponse('Invalid origin', status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    def authorize(x_nexora_token: str | None = Header(default=None)):
        if not x_nexora_token or not secrets.compare_digest(x_nexora_token, token):
            raise HTTPException(401, 'Token local obrigatório')

    auth = Depends(authorize)

    @app.get('/', response_class=HTMLResponse)
    def home():
        s = (UI / 'index.html').read_text(encoding='utf-8')
        return HTMLResponse(s.replace('__LOCAL_TOKEN__', html.escape(token, quote=True)), headers={
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'"})

    @app.get('/app.js')
    def js():
        return FileResponse(UI / 'app.js', media_type='text/javascript')

    @app.get('/styles.css')
    def css():
        return FileResponse(UI / 'styles.css', media_type='text/css')

    @app.get('/api/dashboard', dependencies=[auth])
    def dashboard():
        profiles = store.list_profiles()
        proxy_list = store.list_proxies()
        status = manager.status()
        return {'total': len(profiles), 'running': manager.running(), 'proxies': len(proxy_list),
                'proxy_ok': sum(p['last_status'] == 'ok' for p in proxy_list),
                'max_running': store.settings()['max_running'],
                'statuses': status}

    @app.get('/api/devices', dependencies=[auth])
    def devices():
        return catalog(store)

    @app.post('/api/devices', dependencies=[auth], status_code=201)
    def add_device(data: DeviceInput):
        if data.base_id not in PRESETS:
            raise HTTPException(422, 'O modelo base deve ser um preset oficial do Playwright')
        return store.create_custom_device(data.label, data.base_id, data.width, data.height)

    @app.delete('/api/devices/{device_id}', dependencies=[auth])
    def delete_device(device_id: str):
        try:
            deleted = store.delete_custom_device(device_id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        if not deleted:
            raise HTTPException(404, 'Modelo personalizado não encontrado')
        return {'deleted': True}

    @app.get('/api/profiles', dependencies=[auth])
    def list_profiles():
        result = store.list_profiles()
        state = manager.status()
        for item in result:
            item['status'] = state.get(item['id'], 'stopped')
        return result

    def check_profile(data: ProfileInput, ignore_id=None):
        if data.device_id not in PRESETS and not store.get_custom_device(data.device_id):
            raise HTTPException(422, 'Dispositivo indisponível')
        if data.proxy_id:
            if not store.get_proxy(data.proxy_id):
                raise HTTPException(422, 'Proxy não existe')
            if store.settings()['warn_shared_proxy'] and not data.allow_shared_proxy:
                for item in store.list_profiles():
                    if item['proxy_id'] == data.proxy_id and item['id'] != ignore_id:
                        raise HTTPException(409, 'Este proxy já está associado a outro perfil. Confirme o compartilhamento.')

    @app.post('/api/profiles', dependencies=[auth], status_code=201)
    def create_profile(data: ProfileInput):
        check_profile(data)
        item = store.save_profile(data.model_dump())
        store.log('info', 'profiles', f'Perfil {item["id"]} criado')
        return item

    @app.put('/api/profiles/{profile_id}', dependencies=[auth])
    def update_profile(profile_id: str, data: ProfileInput):
        if not store.get_profile(profile_id):
            raise HTTPException(404, 'Perfil não encontrado')
        if manager.status().get(profile_id) in ('running', 'starting'):
            raise HTTPException(409, 'Encerre o perfil antes de editar')
        check_profile(data, profile_id)
        return store.save_profile(data.model_dump(), profile_id)

    @app.post('/api/profiles/{profile_id}/duplicate', dependencies=[auth], status_code=201)
    def duplicate(profile_id: str):
        orig = store.get_profile(profile_id)
        if not orig:
            raise HTTPException(404, 'Perfil não encontrado')
        orig['name'] += ' (cópia)'
        # A duplicate always starts with empty browser data, not cloned cookies.
        orig['proxy_id'] = None
        return store.save_profile(orig)

    @app.delete('/api/profiles/{profile_id}', dependencies=[auth])
    def delete_profile(profile_id: str):
        if not store.get_profile(profile_id):
            raise HTTPException(404, 'Perfil não encontrado')
        if manager.status().get(profile_id) in ('running', 'starting'):
            raise HTTPException(409, 'Encerre o perfil antes de excluir')
        store.delete_profile(profile_id)
        path = store.profiles_dir / profile_id
        if path.is_dir():
            try:
                shutil.rmtree(path)
            except OSError:
                store.log('error', 'profiles', f'Dados de {profile_id} não puderam ser apagados. Remova manualmente.')
                raise HTTPException(500, 'Perfil removido; falha ao excluir dados locais') from None
        store.log('info', 'profiles', f'Perfil {profile_id} excluído')
        return {'deleted': True}

    async def browser_action(profile_id, method):
        if not store.get_profile(profile_id):
            raise HTTPException(404, 'Perfil não encontrado')
        try:
            return await asyncio.wrap_future(manager.submit(method, profile_id))
        except ValueError as e:
            raise HTTPException(409, str(e)) from None
        except Exception:
            raise HTTPException(503, 'Falha ao controlar o navegador; consulte os logs') from None

    @app.post('/api/profiles/{profile_id}/start', dependencies=[auth])
    async def start(profile_id: str):
        return await browser_action(profile_id, manager.start)

    @app.post('/api/profiles/{profile_id}/stop', dependencies=[auth])
    async def stop(profile_id: str):
        return await browser_action(profile_id, manager.stop)

    @app.get('/api/proxies', dependencies=[auth])
    def proxies():
        return store.list_proxies()

    def validate(data):
        try:
            validate_proxy(data.scheme, data.host, data.port)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @app.post('/api/proxies', dependencies=[auth], status_code=201)
    def add_proxy(data: ProxyInput):
        validate(data)
        obj = store.save_proxy(data.model_dump())
        store.log('info', 'proxy', f'Proxy {obj["id"]} criado')
        return obj

    @app.put('/api/proxies/{proxy_id}', dependencies=[auth])
    def edit_proxy(proxy_id: str, data: ProxyInput):
        validate(data)
        obj = store.save_proxy(data.model_dump(), proxy_id)
        if not obj:
            raise HTTPException(404, 'Proxy não encontrado')
        return obj

    @app.delete('/api/proxies/{proxy_id}', dependencies=[auth])
    def remove_proxy(proxy_id: str):
        if not store.delete_proxy(proxy_id):
            raise HTTPException(404, 'Proxy não encontrado')
        store.log('info', 'proxy', f'Proxy {proxy_id} removido')
        return {'deleted': True}

    @app.post('/api/proxies/import', dependencies=[auth])
    def import_proxies(data: ProxyImport):
        created, errors = [], []
        for index, line in enumerate(data.content.splitlines(), 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            try:
                item = parse_line(line)
                created.append(store.save_proxy(item)['id'])
            except Exception:
                # Do not echo malformed source lines: can contain passwords.
                errors.append({'line': index, 'error': 'Formato ou valores inválidos'})
        store.log('info', 'proxy', f'Importação: {len(created)} proxies válidos, {len(errors)} erros')
        return {'created': len(created), 'errors': errors}

    @app.post('/api/proxies/{proxy_id}/test', dependencies=[auth])
    async def test_proxy(proxy_id: str):
        if not store.get_proxy(proxy_id):
            raise HTTPException(404, 'Proxy não encontrado')
        return await asyncio.wrap_future(manager.submit(manager.test_proxy, proxy_id))

    @app.get('/api/settings', dependencies=[auth])
    def get_settings():
        return store.settings()

    @app.put('/api/settings', dependencies=[auth])
    def update_settings(opts: SettingsInput):
        return store.set_settings(opts.model_dump())

    @app.get('/api/logs', dependencies=[auth])
    def get_logs():
        return store.logs()

    @app.get('/api/diagnostics', dependencies=[auth])
    def diagnostics():
        from playwright import __file__ as pwfile
        import platform
        import shutil as sh
        import psutil
        vm = psutil.virtual_memory()
        return {'system': platform.platform(), 'python': platform.python_version(),
                'playwright_location': str(Path(pwfile).parent),
                'chromium_override': bool(os.getenv('NEXORA_CHROMIUM_PATH')),
                'chromium_system': sh.which('chromium') or sh.which('chrome') or 'não localizado',
                'headless': headless, 'data_dir': str(store.root),
                'ram_total_mb': round(vm.total / (1024**2)), 'ram_available_mb': round(vm.available / (1024**2)),
                'cpu_percent': psutil.cpu_percent(interval=None), 'logical_cpu_count': psutil.cpu_count(),
                'note': 'Emulação de navegador, não dispositivos reais. Safari depende de Playwright WebKit.'}
    return app
