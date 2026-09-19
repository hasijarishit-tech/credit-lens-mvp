"""Fetches a public web page and strips it to plain text for the source-link
and name-search intake paths. Deliberately conservative: only public
http(s) pages, with basic SSRF guards (no fetching internal/private
network addresses via a user-supplied URL).
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

MAX_RESPONSE_BYTES = 5_000_000
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "CreditLens/0.1 (hackathon MVP; +financial-statement-extraction)"


class WebFetchError(Exception):
    pass


def _assert_public_host(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise WebFetchError(f"Could not resolve host '{hostname}'.") from e

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise WebFetchError("This URL points to a non-public address, which isn't allowed.")


def fetch_page_text(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise WebFetchError("Only http(s) URLs are supported.")
    if not parsed.hostname:
        raise WebFetchError("That doesn't look like a valid URL.")

    _assert_public_host(parsed.hostname)

    try:
        with httpx.Client(
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise WebFetchError(f"The page returned an error ({e.response.status_code}).") from e
    except httpx.RequestError as e:
        raise WebFetchError(f"Couldn't reach that page: {e}") from e

    if len(response.content) > MAX_RESPONSE_BYTES:
        raise WebFetchError("That page is too large to process.")

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise WebFetchError(
            "That URL didn't return an HTML page (it may be behind a login wall or "
            "not a page this tool can read). Try the PDF upload or manual entry instead."
        )

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    if len(text) < 100:
        raise WebFetchError(
            "Couldn't find readable text on that page (it may render its content via "
            "JavaScript or embed numbers as an image/chart). Try the PDF upload or "
            "manual entry instead."
        )
    return text
