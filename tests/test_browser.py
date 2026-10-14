"""Actual browser launch and profile data separation (Chromium installed required)."""
import os
import shutil
import pytest
from nexora.storage import Store
from nexora.browser import BrowserManager
import time


@pytest.mark.skipif(not (os.getenv('NEXORA_CHROMIUM_PATH') or shutil.which('chromium')),reason='Installed Chromium not available')
def test_browser_persistence_and_limit(tmp_path,monkeypatch):
    path=os.getenv('NEXORA_CHROMIUM_PATH') or shutil.which('chromium')
    monkeypatch.setenv('NEXORA_CHROMIUM_PATH',path)
    store=Store(tmp_path)
    store.set_settings({'max_running':1})
    payload={'name':'P','device_id':'pixel-5','width':393,'height':727,
             'locale':'pt-BR','timezone':'America/Sao_Paulo','tags':[], 'group_name':'','proxy_id':None}
    a=store.save_profile(payload)['id']
    b=store.save_profile({**payload,'name':'B'})['id']
    bm=BrowserManager(store,headless=True)
    try:
        assert bm.submit(bm.start,a).result(timeout=40)['status']=='running'
        # about:blank cannot persist localStorage; cookies can be added to context.
        def write_cookie():
            bm._contexts[a].add_cookies([{'name':'nexora-session','value':'only-A',
              'url':'https://example.com','expires':int(time.time())+3600}])
        bm.submit(write_cookie).result(timeout=10)
        with pytest.raises(ValueError,match='Limite'):
            bm.submit(bm.start,b).result(timeout=10)
        assert bm.submit(bm.stop,a).result(timeout=10)['status']=='stopped'
        assert bm.submit(bm.start,b).result(timeout=40)['status']=='running'
        def read_b():return bm._contexts[b].cookies('https://example.com')
        assert not any(c['name']=='nexora-session' for c in bm.submit(read_b).result(timeout=10))
        bm.submit(bm.stop,b).result(timeout=10)
        assert bm.submit(bm.start,a).result(timeout=40)['status']=='running'
        def read_a():return bm._contexts[a].cookies('https://example.com')
        assert any(c['name']=='nexora-session' and c['value']=='only-A' for c in bm.submit(read_a).result(timeout=10))
    finally:
        bm.close()
