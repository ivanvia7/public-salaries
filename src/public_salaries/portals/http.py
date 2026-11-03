import time
from importlib.metadata import version
from typing import Any
from urllib.parse import urlsplit

import httpx

USER_AGENT = (
    f"public-salaries/{version('public-salaries')}"
    " (+https://github.com/ivanvia7/public-salaries)"
)
MIN_GAP_SECONDS = 1.0
RETRY_STATUSES = {429, 500, 502, 503, 504}
# A New York year is 11 pages of 50,000 rows; a slow answer now and then is
# normal, so a call gets 5 tries over about 50 seconds.
ATTEMPTS = 5
RETRY_SECONDS = 5.0
MAX_RETRY_SECONDS = 60.0

# IPv4 only: an IPv6 fallback on some networks hides the real connect error.
CLIENT = httpx.Client(
    headers={"User-Agent": USER_AGENT},
    # A 50,000-row page can take well over the usual 5 seconds.
    timeout=120,
    follow_redirects=True,
    transport=httpx.HTTPTransport(local_address="0.0.0.0"),
)
_last_call: dict[str, float] = {}


def wait_turn(host: str) -> None:
    gap = time.monotonic() - _last_call.get(host, 0.0)
    if gap < MIN_GAP_SECONDS:
        time.sleep(MIN_GAP_SECONDS - gap)
    _last_call[host] = time.monotonic()


def retry_delay(response: httpx.Response, attempt: int) -> float:
    after = response.headers.get("Retry-After", "")
    wait = float(after) if after.isdigit() else RETRY_SECONDS * attempt
    return min(wait, MAX_RETRY_SECONDS)


def get_json(url: str, params: dict[str, str], headers: dict[str, str]) -> Any:
    attempt = 1
    while True:
        wait_turn(urlsplit(url).netloc)
        try:
            response = CLIENT.get(url, params=params, headers=headers)
        except httpx.TransportError as error:
            if attempt == ATTEMPTS:
                raise RuntimeError(
                    f"{error!r} from {url} after {ATTEMPTS} tries"
                ) from error
            time.sleep(RETRY_SECONDS * attempt)
        else:
            if response.status_code not in RETRY_STATUSES or attempt == ATTEMPTS:
                break
            time.sleep(retry_delay(response, attempt))
        attempt += 1

    if response.is_error:
        raise RuntimeError(
            f"{response.status_code} from {response.url}: {response.text[:300]}"
        )

    try:
        return response.json()
    except ValueError as error:
        raise RuntimeError(
            f"not JSON from {response.url}: {response.text[:300]}"
        ) from error
