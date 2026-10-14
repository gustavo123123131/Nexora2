"""Playwright device presets; browser emulation, not physical devices."""
from playwright.sync_api import sync_playwright

# Resolve against the installed Playwright catalog (no invented UA strings).
PRESETS = {
    'pixel-7': {'label': 'Google Pixel 7', 'engine': 'chromium', 'device': 'Pixel 7', 'family': 'Android / Chrome'},
    'pixel-5': {'label': 'Google Pixel 5', 'engine': 'chromium', 'device': 'Pixel 5', 'family': 'Android / Chrome'},
    'galaxy-s9': {'label': 'Samsung Galaxy S9+', 'engine': 'chromium', 'device': 'Galaxy S9+', 'family': 'Android / Chrome'},
    'iphone-13': {'label': 'Apple iPhone 13', 'engine': 'webkit', 'device': 'iPhone 13', 'family': 'iPhone / Safari (WebKit)'},
    'iphone-14-pro': {'label': 'Apple iPhone 14 Pro', 'engine': 'webkit', 'device': 'iPhone 14 Pro', 'family': 'iPhone / Safari (WebKit)'},
    'iphone-15-pro': {'label': 'Apple iPhone 15 Pro', 'engine': 'webkit', 'device': 'iPhone 15 Pro', 'family': 'iPhone / Safari (WebKit)'},
}


def catalog(store=None):
    with sync_playwright() as p:
        result = [{**{'id': key, 'custom': False}, **entry,
                  'viewport': p.devices[entry['device']]['viewport'],
                  'device_scale_factor': p.devices[entry['device']]['device_scale_factor']}
                  for key, entry in PRESETS.items() if entry['device'] in p.devices]
        if store:
            for c in store.list_custom_devices():
                base = next((item for item in result if item['id'] == c['base_id']), None)
                if base:
                    result.append({**base, 'id': c['id'], 'label': c['label'],
                                   'custom': True, 'base_id': c['base_id'],
                                   'viewport': {'width': c['width'], 'height': c['height']}})
        return result


def resolve(p, preset_id, store=None):
    preset = PRESETS.get(preset_id)
    if not preset and store:
        custom = store.get_custom_device(preset_id)
        if custom:
            preset = PRESETS.get(custom['base_id'])
    if not preset or preset['device'] not in p.devices:
        raise ValueError('Modelo de dispositivo indisponível nesta versão do Playwright')
    return preset, dict(p.devices[preset['device']])
