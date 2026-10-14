"""Smoke test dashboard/forms in a browser with mocked API transport.

This tests frontend interactions; API routes are tested independently in test_app.py.
"""
import os
import shutil
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(not (os.getenv('NEXORA_CHROMIUM_PATH') or shutil.which('chromium')), reason='Chromium executable not available')
def test_dashboard_create_form_and_devices():
    browser_path = os.getenv('NEXORA_CHROMIUM_PATH') or shutil.which('chromium')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=browser_path)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        try:
            html=(ROOT/'ui/index.html').read_text(encoding='utf-8').replace('__LOCAL_TOKEN__','mocked-token')
            page.set_content(html)
            page.add_style_tag(path=str(ROOT/'ui/styles.css'))
            page.evaluate('''() => {
              const profiles=[];
              const device={id:'pixel-7',label:'Pixel 7',engine:'chromium',family:'Android / Chrome',
                viewport:{width:412,height:839},device_scale_factor:2.625};
              window.fetch=async (url,opts={})=>{
                let data=[];const method=opts.method||'GET';
                if(url.endsWith('/profiles')){
                  if(method==='POST') { const profile=JSON.parse(opts.body);profiles.push({...profile,id:'test-id',status:'stopped'});data=profiles.at(-1); }
                  else data=profiles;
                } else if(url.endsWith('/proxies')) data=[];
                else if(url.endsWith('/devices')) data=[device];
                else if(url.endsWith('/dashboard')) data={total:profiles.length,running:0,proxies:0,proxy_ok:0,max_running:3,statuses:{}};
                else if(url.endsWith('/settings')) data={max_running:3,warn_shared_proxy:true,min_free_mb:512};
                return {ok:true,json:async()=>data};
              };
            }''')
            page.add_script_tag(path=str(ROOT/'ui/app.js'))
            page.wait_for_function("document.querySelector('h1')?.textContent==='Visão geral'")
            page.get_by_role('button', name='Novo perfil').click()
            page.locator('#field-name').fill('QA Mobile')
            page.get_by_role('button', name='Criar perfil').click()
            page.get_by_role('button', name='Perfis', exact=False).first.click()
            page.wait_for_function("document.querySelector('h1')?.textContent==='Perfis de navegador'")
            assert page.get_by_text('QA Mobile').count() == 1
            page.get_by_role('button', name='Dispositivos').click()
            page.get_by_role('button', name='Novo modelo').click()
            assert page.locator('#deviceForm').count() == 1
            assert not errors, errors
        finally:
            browser.close()
