from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from nexora.api import create_app
from nexora.proxies import parse_line


@pytest.fixture
def setup(tmp_path):
    app=create_app(tmp_path,headless=True)
    with TestClient(app) as client:
        h={'X-Nexora-Token':app.state.token}
        yield client,h,tmp_path


def device(client,h):
    res=client.get('/api/devices',headers=h)
    assert res.status_code==200, res.text
    items=res.json()
    assert len(items)>0
    return items[0]


def profile_payload(dev,**kwargs):
    return dict(name='A',device_id=dev['id'],width=dev['viewport']['width'],height=dev['viewport']['height'],locale='pt-BR',timezone='America/Sao_Paulo',tags=['teste'],group_name='QA',proxy_id=None,**kwargs)


def test_profile_lifecycle(setup):
    c,h,root=setup
    dev=device(c,h)
    p=c.post('/api/profiles',headers=h,json=profile_payload(dev))
    assert p.status_code==201,p.text
    profile=p.json()
    assert len(profile['id'])==36
    assert c.get('/api/profiles',headers=h).json()[0]['status']=='stopped'
    d=c.post('/api/profiles/'+profile['id']+'/duplicate',headers=h)
    assert d.status_code==201
    assert d.json()['id']!=profile['id']
    assert d.json()['name']=='A (cópia)'
    update={**profile_payload(dev),'name':'renamed'}
    assert c.put('/api/profiles/'+profile['id'],headers=h,json=update).json()['name']=='renamed'
    assert c.delete('/api/profiles/'+profile['id'],headers=h).status_code==200
    assert c.delete('/api/profiles/'+profile['id'],headers=h).status_code==404
    assert len(c.get('/api/profiles',headers=h).json())==1


def test_persistence_and_profile_directories(setup):
    c,h,root=setup
    dev=device(c,h)
    a=c.post('/api/profiles',headers=h,json=profile_payload(dev)).json()
    b=c.post('/api/profiles',headers=h,json={**profile_payload(dev),'name':'B'}).json()
    dir_a=root/'browser-profiles'/a['id']
    dir_b=root/'browser-profiles'/b['id']
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a/'cookies.txt').write_text('a')
    (dir_b/'cookies.txt').write_text('b')
    assert c.delete('/api/profiles/'+a['id'],headers=h).status_code==200
    assert not dir_a.exists()
    assert (dir_b/'cookies.txt').read_text()=='b'
    app2=create_app(root,headless=True)
    with TestClient(app2) as c2:
        assert len(c2.get('/api/profiles',headers={'X-Nexora-Token':app2.state.token}).json())==1


def test_security(setup):
    c,h,_=setup
    assert c.get('/api/profiles').status_code==401
    assert c.get('/api/profiles',headers={'X-Nexora-Token':'wrong'}).status_code==401
    assert c.get('/api/profiles',headers={**h,'Origin':'https://attacker.example'}).status_code==403
    assert c.get('/api/profiles',headers={**h,'Host':'attacker.example'}).status_code==403
    assert c.get('/').status_code==200
    assert 'NEXORA' in c.get('/').text
    assert c.get('/app.js').status_code==200
    assert c.get('/styles.css').status_code==200
    assert c.post('/api/profiles',headers=h,json={'name':'x'}).status_code==422


def test_proxy_import_and_redaction(setup):
    c,h,root=setup
    res=c.post('/api/proxies/import',headers=h,json={'content':'example.com:8080:user:supersecret\n# hi\nsocks5://u:p@localhost:1080\nmalformed:abc'})
    assert res.status_code==200
    assert res.json()['created']==2
    assert res.json()['errors']==[{'line':4,'error':'Formato ou valores inválidos'}]
    listed=c.get('/api/proxies',headers=h).json()
    assert len(listed)==2
    assert all('password' not in p and 'password_enc' not in p for p in listed)
    assert 'supersecret' not in str(c.get('/api/logs',headers=h).json())
    p=c.post('/api/proxies',headers=h,json={'name':'x','scheme':'http','host':'localhost','port':8000,'password':'anothersecret'}).json()
    assert p['has_password']
    old_id=p['id']
    c.put('/api/proxies/'+old_id,headers=h,json={'name':'y','scheme':'http','host':'localhost','port':8001,'password':None})
    assert c.app.state.store.get_proxy(old_id,reveal=True)['password']=='anothersecret'
    assert b'anothersecret' not in (root/'nexora.db').read_bytes()


def test_proxy_assignment_warning(setup):
    c,h,_=setup
    dev=device(c,h)
    proxy=c.post('/api/proxies',headers=h,json={'name':'P','scheme':'http','host':'localhost','port':8989}).json()
    data={**profile_payload(dev),'proxy_id':proxy['id']}
    assert c.post('/api/profiles',headers=h,json=data).status_code==201
    assert c.post('/api/profiles',headers=h,json=data).status_code==409
    assert c.post('/api/profiles',headers=h,json={**data,'allow_shared_proxy':True}).status_code==201
    assert c.delete('/api/proxies/'+proxy['id'],headers=h).status_code==200
    assert all(not p['proxy_id'] for p in c.get('/api/profiles',headers=h).json())


def test_settings_and_limit(setup):
    c,h,_=setup
    assert c.put('/api/settings',headers=h,json={'max_running':0,'warn_shared_proxy':True}).status_code==422
    assert c.put('/api/settings',headers=h,json={'max_running':1,'warn_shared_proxy':False}).status_code==200
    assert c.get('/api/dashboard',headers=h).json()['max_running']==1


def test_parser():
    assert parse_line('example.org:8111:user:pass:with:colons')['password']=='pass:with:colons'
    assert parse_line('[::1]:1080')['host']=='::1'
    assert parse_line('socks5://alice:p%40ss@localhost:1080')['password']=='p@ss'
    with pytest.raises(ValueError):parse_line('evil:0')
    with pytest.raises(ValueError):parse_line('bad host:1111')
