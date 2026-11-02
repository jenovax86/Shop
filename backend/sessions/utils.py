from ua_parser import parse


def __get_version(value):
    if value is None:
        return None

    parts = [
        value.major,
        value.minor,
        value.patch,
        value.patch_minor
    ]
    version = ".".join(
        part for part in parts if part
    )
    return version


def parse_user_agent(user_agent: str) -> dict:
    result = parse(user_agent)

    browser = result.user_agent
    os = result.os
    device = result.device

    return {
        "browser": browser.family if browser else None,
        "browser_version": __get_version(browser),
        "os": os.family if os else None,
        "os_version": __get_version(os),
        "device": device.family if device else None,
        "device_brand": device.brand if device else None,
        "device_model": device.model if device else None,
    }
