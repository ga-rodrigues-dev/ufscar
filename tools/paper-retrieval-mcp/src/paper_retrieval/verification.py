"""Recognize the observed verification gate and perform bounded PoW v1 work.

Protocol reference: https://github.com/altcha-org/altcha-lib-py#pow-v1-legacy
No JavaScript from the response is executed.
"""

import base64
import hashlib
import json
import re
import time

from bs4 import BeautifulSoup


def verification_paths(content: bytes) -> tuple[str, str] | None:
    soup = BeautifulSoup(content, "html.parser")
    for widget in soup.select("altcha-widget[challengeurl]"):
        path = widget.get("challengeurl", "")
        if re.fullmatch(r"/captcha/challenge/[0-9]+", path):
            solution = path.replace("/challenge/", "/solution/")
            if solution in content.decode("utf-8", errors="replace"):
                return path, solution
    return None


def is_verification_page(content: bytes) -> bool:
    soup = BeautifulSoup(content, "html.parser")
    if any(re.fullmatch(r"/captcha/challenge/[0-9]+", tag.get("challengeurl", ""))
           for tag in soup.select("altcha-widget[challengeurl]")):
        return True
    if soup.select_one(".g-recaptcha, .h-captcha, .cf-turnstile"):
        return True
    title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
    return any(marker in title for marker in (
        "проверка на робота", "checking your browser", "verify you are human", "ddos-guard",
    ))


def solve_work(challenge: dict, *, max_steps: int = 2_000_000, max_seconds: float = 10) -> str:
    if not isinstance(challenge, dict) or challenge.get("algorithm") != "SHA-256":
        raise ValueError("unsupported_challenge")
    maximum = challenge.get("maxNumber", challenge.get("maxnumber", 1_000_000))
    if type(maximum) is not int or not 0 <= maximum <= max_steps:
        raise ValueError("work_limit_exceeded")
    for key, limit in (("salt", 512), ("signature", 1024), ("challenge", 64)):
        if not isinstance(challenge.get(key), str) or not 0 < len(challenge[key]) <= limit:
            raise ValueError("invalid_challenge")
    target = challenge["challenge"].lower()
    if re.fullmatch(r"[0-9a-f]{64}", target) is None:
        raise ValueError("invalid_challenge")
    started = time.monotonic()
    salt = challenge["salt"].encode()
    for number in range(maximum + 1):
        if number % 1024 == 0 and time.monotonic() - started >= max_seconds:
            raise ValueError("work_time_limit_exceeded")
        if hashlib.sha256(salt + str(number).encode()).hexdigest() == target:
            payload = {key: challenge[key] for key in ("algorithm", "challenge", "salt", "signature")}
            payload.update(number=number, took=int((time.monotonic() - started) * 1000))
            return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    raise ValueError("unsolved_challenge")
