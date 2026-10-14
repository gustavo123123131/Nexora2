"""Regressions for failed browser initialization and process cleanup."""
from types import SimpleNamespace

import pytest

from nexora.browser import BrowserManager
from nexora.storage import Store


def test_partial_launch_closes_context_and_redacts_driver_error(tmp_path, monkeypatch):
    store = Store(tmp_path)
    profile = store.save_profile({
        'name': 'Teste', 'device_id': 'pixel-5', 'width': 393, 'height': 727,
        'locale': 'pt-BR', 'timezone': 'America/Sao_Paulo',
        'tags': [], 'group_name': '', 'proxy_id': None,
    })
    profile_id = profile['id']
    leaked_secret = 'proxy-password-do-not-log'

    class FailingContext:
        pages = []

        def __init__(self):
            self.close_calls = 0
            self.on_close = None

        def on(self, event, callback):
            assert event == 'close'
            self.on_close = callback

        def new_page(self):
            raise RuntimeError('sensitive driver output: ' + leaked_secret)

        def close(self):
            self.close_calls += 1
            if self.on_close:
                self.on_close()

    ctx = FailingContext()
    seen_options = {}
    def launch_persistent_context(**kwargs):
        seen_options.update(kwargs)
        return ctx

    monkeypatch.setattr('nexora.browser.resolve', lambda *_: (
        {'engine': 'chromium'}, {'viewport': {'width': 393, 'height': 727}}
    ))
    manager = BrowserManager(store, headless=True)
    manager._get_playwright = lambda: SimpleNamespace(
        chromium=SimpleNamespace(launch_persistent_context=launch_persistent_context)
    )
    try:
        with pytest.raises(RuntimeError, match='Falha de conexão/inicialização'):
            manager.submit(manager.start, profile_id).result(timeout=10)
        assert ctx.close_calls == 1
        assert profile_id not in manager._contexts
        assert manager.status()[profile_id] == 'stopped'
        assert seen_options['timeout'] == 60000
        assert seen_options['user_data_dir'].endswith(profile_id)
        assert leaked_secret not in str(store.logs())
        assert manager.running() == 0
    finally:
        manager.close()
