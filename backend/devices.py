"""Device catalog uses the Playwright installed presets, not invented fingerprints."""
PREFERRED = ("iPhone 13", "iPhone 13 Pro", "iPhone 14",
             "iPhone 15", "Pixel 5", "Pixel 7", "Galaxy S9+")


def catalog(driver):
    return [{"name": n,
             "browser": driver.devices[n].get("default_browser_type", "chromium"),
             "viewport": driver.devices[n]["viewport"]}
            for n in PREFERRED if n in driver.devices]


def supported(driver, name):
    return name in {item["name"] for item in catalog(driver)}
