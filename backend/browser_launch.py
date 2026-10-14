"""Isolated persistent browser launch with documented mobile emulation."""
import os


async def launch(driver, profile, proxy, secrets, directory):
    desc = dict(driver.devices[profile["device"]])
    engine = desc.pop("default_browser_type", "chromium")
    if engine not in ("chromium", "webkit"):
        raise ValueError("Unsupported mobile browser engine")
    if profile.get("viewport_width") and profile.get("viewport_height"):
        vp = {"width": profile["viewport_width"], "height": profile["viewport_height"]}
        desc["viewport"] = vp
        desc["screen"] = vp
    desc["locale"] = profile["locale"]
    desc["timezone_id"] = profile["timezone"]
    if proxy:
        if proxy["scheme"] == "socks5" and proxy.get("username"):
            raise ValueError("Authenticated SOCKS5 browser proxy not supported")
        host = proxy["host"]
        if ":" in host and not host.startswith("["):
            host = "[" + host + "]"
        settings = {"server": f'{proxy["scheme"]}://{host}:{proxy["port"]}'}
        if proxy.get("username"):
            settings["username"] = proxy["username"]
            password = secrets.get(proxy["id"])
            if not password:
                raise ValueError("Proxy password unavailable in system vault")
            settings["password"] = password
        desc["proxy"] = settings
    directory.mkdir(parents=True, exist_ok=True)
    context = await getattr(driver, engine).launch_persistent_context(
        user_data_dir=str(directory),
        headless=os.getenv("NEXORA_HEADLESS", "false").lower() == "true",
        timeout=45000, **desc
    )
    if not context.pages:
        await context.new_page()
    return context
