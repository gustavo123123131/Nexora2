"""Playwright contexts on a dedicated thread to respect sync API thread ownership."""
import os
import shutil
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from .devices import resolve
from .proxies import playwright_options, safe_error


class BrowserManager:
    def __init__(self, store, headless=False):
        self.store = store
        self.headless = headless
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='nexora-browser')
        self._playwright = None
        self._contexts = {}
        self._states = {}
        self._lock = threading.Lock()

    def status(self):
        with self._lock:
            return dict(self._states)

    def running(self):
        with self._lock:
            return sum(v == 'running' for v in self._states.values())

    def _set(self, key, value):
        with self._lock:
            self._states[key] = value

    def submit(self, fn, *args):
        return self._executor.submit(fn, *args)

    def _get_playwright(self):
        if self._playwright is None:
            self._playwright = sync_playwright().start()
        return self._playwright

    def _on_closed(self, profile_id):
        self._contexts.pop(profile_id, None)
        self._set(profile_id, 'stopped')

    def start(self, profile_id):
        if profile_id in self._contexts:
            return {'status': 'running'}
        item = self.store.get_profile(profile_id)
        if not item:
            raise ValueError('Perfil não encontrado')
        limit = self.store.settings()['max_running']
        if self.running() >= limit:
            raise ValueError(f'Limite de {limit} perfis simultâneos atingido')
        self._set(profile_id, 'starting')
        try:
            p = self._get_playwright()
            preset, device = resolve(p, item['device_id'])
            device.pop('default_browser_type', None)
            device.update(viewport={'width': item['width'], 'height': item['height']},
                          locale=item['locale'], timezone_id=item['timezone'])
            engine = getattr(p, preset['engine'])
            opts = {'headless': self.headless, **device, 'user_data_dir':
                    str(self.store.profiles_dir / profile_id)}
            # Browser executable discovery is opt-in for Chromium (system install)
            # to avoid downloading Chromium twice on some Linux distributions.
            executable = os.environ.get('NEXORA_CHROMIUM_PATH')
            if preset['engine'] == 'chromium' and executable:
                opts['executable_path'] = executable
            proxy = self.store.get_proxy(item['proxy_id'], reveal=True) if item['proxy_id'] else None
            if item['proxy_id'] and proxy is None:
                raise ValueError('Proxy associado não existe')
            if proxy:
                opts['proxy'] = playwright_options(proxy)
            ctx = engine.launch_persistent_context(**opts)
            self._contexts[profile_id] = ctx
            ctx.on('close', lambda: self._on_closed(profile_id))
            if not ctx.pages:
                ctx.new_page()
            self._set(profile_id, 'running')
            self.store.log('info', 'browser', f'Perfil {profile_id} iniciado')
            return {'status': 'running'}
        except Exception as exc:
            self._set(profile_id, 'stopped')
            self.store.log('error', 'browser', f'Perfil {profile_id}: {safe_error(exc)}')
            if isinstance(exc, ValueError):
                raise
            raise RuntimeError(safe_error(exc)) from None

    def stop(self, profile_id):
        ctx = self._contexts.pop(profile_id, None)
        if ctx:
            try:
                ctx.close()
            except Exception as exc:
                self.store.log('warning', 'browser', f'Perfil {profile_id}: {safe_error(exc)}')
        self._set(profile_id, 'stopped')
        return {'status': 'stopped'}

    def stop_all(self):
        for key in list(self._contexts):
            self.stop(key)
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def close(self):
        try:
            self.submit(self.stop_all).result(timeout=25)
        finally:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def test_proxy(self, proxy_id):
        proxy = self.store.get_proxy(proxy_id, reveal=True)
        if not proxy:
            raise ValueError('Proxy não encontrado')
        browser = None
        try:
            p = self._get_playwright()
            kwargs = {'headless': True, 'proxy': playwright_options(proxy)}
            path = os.environ.get('NEXORA_CHROMIUM_PATH')
            if path:
                kwargs['executable_path'] = path
            browser = p.chromium.launch(**kwargs)
            page = browser.new_page()
            response = page.goto('https://api.ipify.org?format=json', timeout=15000, wait_until='domcontentloaded')
            if not response or not response.ok:
                raise RuntimeError('Endpoint de teste indisponível')
            addr = json.loads(page.locator('body').inner_text())['ip']
            self.store.set_proxy_test(proxy_id, 'ok', addr)
            return {'status': 'ok', 'ip': addr}
        except Exception as exc:
            msg = safe_error(exc)
            self.store.set_proxy_test(proxy_id, 'error', error=msg)
            self.store.log('warning', 'proxy', f'Proxy {proxy_id}: {msg}')
            return {'status': 'error', 'error': msg}
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
