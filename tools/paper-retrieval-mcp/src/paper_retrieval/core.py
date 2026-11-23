"""Bounded retrieval, PDF validation, cache and local acquisition records."""

from __future__ import annotations

import asyncio
import errno
import hashlib
import io
import ipaddress
import json
import logging
import math
import os
import re
import ssl
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict
from pypdf import PdfReader

from .network import HostRoutingTransport
from .verification import is_verification_page, solve_work, verification_paths


MESSAGES = {
    "invalid_doi": "Provide a valid DOI or an https://doi.org/ DOI URL.",
    "unconfigured": "Paper retrieval is not configured. Contact the server operator.",
    "unavailable": "The paper could not be retrieved. Try again later or use another DOI.",
    "network_permission_denied": "The execution environment denied network access. Request network permission and retry once.",
    "connection_failed": "A connection could not be established. Check network access or contact the operator.",
    "tls_failed": "The secure connection could not be established. Contact the operator; keep certificate verification enabled.",
    "verification_required": "The retrieval service requires verification that this client could not complete.",
    "rate_limited": "The retrieval service rate limit was reached. Try again later.",
    "access_denied": "The retrieval service denied access.",
    "not_found": "The retrieval endpoint returned not found. This does not establish that the article does not exist.",
    "upstream_error": "The retrieval service returned an unsuccessful response.",
    "no_pdf_link": "The response did not contain a PDF download link.",
    "invalid_document": "The downloaded response was not a readable, unencrypted PDF with pages.",
    "destination_not_allowed": "A download destination is not allowed by the operator configuration.",
    "response_too_large": "The downloaded response exceeded the configured size limit.",
    "timeout": "Paper retrieval exceeded its time limit. Try again later.",
    "missing": "The paper is not in the local collection. Retrieve it by DOI first.",
    "internal": "Paper retrieval failed. Contact the server operator.",
}


class RetrievalError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(MESSAGES.get(code, MESSAGES["unavailable"]))


def exception_chain(error: BaseException):
    pending, seen = [error], set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        pending.extend(child for child in (
            current.__cause__, current.__context__, *getattr(current, "exceptions", ()),
        ) if child is not None)


def failure_code(error: Exception) -> str:
    if isinstance(error, RetrievalError):
        return error.code
    causes = list(exception_chain(error))
    if any(isinstance(item, PermissionError) or isinstance(item, OSError)
           and item.errno in {errno.EACCES, errno.EPERM} for item in causes):
        return "network_permission_denied"
    if any(isinstance(item, ssl.SSLError) for item in causes):
        return "tls_failed"
    if isinstance(error, httpx.TimeoutException):
        return "timeout"
    if isinstance(error, (httpx.ConnectError, httpx.ProxyError)):
        return "connection_failed"
    if isinstance(error, httpx.HTTPStatusError):
        return {401: "access_denied", 403: "access_denied", 404: "not_found", 429: "rate_limited"}.get(
            error.response.status_code, "upstream_error",
        )
    return "unavailable"


def normalize_doi(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("doi:"):
        value = value[4:].strip()
    if value.lower().startswith(("http://", "https://")):
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or parsed.netloc.lower() not in {"doi.org", "dx.doi.org"}
            or parsed.query or parsed.fragment
        ):
            raise RetrievalError("invalid_doi")
        value = unquote(parsed.path.lstrip("/"))
    if (
        len(value) > 2048
        or re.fullmatch(r"10\.\d{4,9}/[^\s\x00-\x1f\x7f<>\"]+", value) is None
    ):
        raise RetrievalError("invalid_doi")
    return value.lower()


def safe_url(url: str) -> str:
    """Accept operator-selected public HTTPS origins without embedded credentials."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https" or not parsed.hostname
        or parsed.username or parsed.password or parsed.port not in {None, 443}
        or parsed.query or parsed.fragment
        or any(char.isspace() or ord(char) < 32 for char in url)
    ):
        raise ValueError("Provider URLs must be HTTPS URLs without credentials or query strings.")
    host = parsed.hostname.lower()
    if "." not in host or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Provider host must be a public hostname.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ValueError("Private provider addresses are not supported.")
    return url.rstrip("/")


@dataclass(frozen=True)
class Settings:
    provider_urls: tuple[str, ...] = ()
    extra_hosts: tuple[str, ...] = ()
    proxy_url: str | None = field(default=None, repr=False)
    host_overrides: dict[str, str] = field(default_factory=dict)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / ".data")
    request_timeout: float = 20
    retrieval_timeout: float = 90
    max_pdf_bytes: int = 32 * 1024 * 1024
    max_html_bytes: int = 2 * 1024 * 1024

    def __post_init__(self) -> None:
        for url in self.provider_urls:
            safe_url(url)
        for host in self.extra_hosts:
            if urlsplit(safe_url("https://" + host)).netloc != host:
                raise ValueError("Allowed hosts must be exact hostnames without paths or ports.")
        if self.proxy_url is not None:
            try:
                proxy = urlsplit(self.proxy_url)
                if (
                    proxy.scheme not in {"http", "https", "socks5", "socks5h"}
                    or not proxy.hostname or proxy.fragment or proxy.query
                    or proxy.path not in {"", "/"}
                    or proxy.port == 0
                    or any(char.isspace() or ord(char) < 32 for char in self.proxy_url)
                ):
                    raise ValueError
            except ValueError:
                raise ValueError("Invalid proxy configuration.") from None
        if not isinstance(self.host_overrides, dict):
            raise ValueError("Host overrides must be a JSON object.")
        if self.host_overrides and self.proxy_url:
            raise ValueError("Configure either a proxy or host overrides.")
        for host, address in self.host_overrides.items():
            if host not in self.allowed_hosts or not isinstance(address, str):
                raise ValueError("Host overrides must refer to configured allowed hosts.")
            try:
                if not ipaddress.ip_address(address).is_global:
                    raise ValueError
            except ValueError:
                raise ValueError("Host overrides require public IP addresses.") from None
        for value in (self.request_timeout, self.retrieval_timeout):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Timeouts must be finite positive numbers.")
        if self.max_pdf_bytes <= 0 or self.max_html_bytes <= 0:
            raise ValueError("Response size limits must be positive.")

    @classmethod
    def from_env(cls) -> Settings:
        def entries(name: str) -> tuple[str, ...]:
            return tuple(item.strip() for item in os.environ.get(name, "").split(",") if item.strip())

        options = dict(
            provider_urls=entries("PAPER_PROVIDER_URLS"),
            extra_hosts=entries("PAPER_ALLOWED_HOSTS"),
            proxy_url=os.environ.get("PAPER_PROXY_URL") or None,
            host_overrides=json.loads(os.environ.get("PAPER_HOST_OVERRIDES", "{}")),
            request_timeout=float(os.environ.get("PAPER_REQUEST_TIMEOUT", "20")),
            retrieval_timeout=float(os.environ.get("PAPER_RETRIEVAL_TIMEOUT", "90")),
            max_pdf_bytes=int(os.environ.get("PAPER_MAX_PDF_BYTES", str(32 * 1024 * 1024))),
        )
        if os.environ.get("PAPER_DATA_DIR"):
            options["data_dir"] = Path(os.environ["PAPER_DATA_DIR"]).expanduser().resolve()
        return cls(**options)

    @property
    def allowed_hosts(self) -> frozenset[str]:
        return frozenset(
            [urlsplit(url).hostname.lower() for url in self.provider_urls]
            + [host.lower() for host in self.extra_hosts]
        )


class PaperResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    doi: str
    paper_id: str
    file_path: str
    resource_uri: str
    mime_type: str = "application/pdf"
    size_bytes: int
    sha256: str
    page_count: int
    cached: bool


@dataclass(frozen=True)
class Document:
    content: bytes
    landing_url: str
    download_url: str
    page_count: int


def validate_pdf(content: bytes) -> int:
    if not content.startswith(b"%PDF-"):
        raise RetrievalError("invalid_document")
    try:
        # Published PDFs can contain recoverable defects such as duplicate
        # dictionary keys. The exported copy is rewritten and checked strictly.
        reader = PdfReader(io.BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF")
        count = len(reader.pages)
        if count == 0:
            raise ValueError("Empty PDF")
        return count
    except Exception:
        raise RetrievalError("invalid_document") from None


def pdf_candidates(html: bytes, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for selector, attribute in (
        ('meta[name="citation_pdf_url"][content]', "content"),
        ('link[type="application/pdf"][href]', "href"),
        ("iframe[src]", "src"), ("embed[src]", "src"),
        ("object[data]", "data"), ("a[href]", "href"),
    ):
        for tag in soup.select(selector):
            target = tag.get(attribute, "")
            if (
                selector == "a[href]"
                and not urlsplit(target).path.lower().endswith(".pdf")
                and tag.get("type", "").lower() != "application/pdf"
            ):
                continue
            url = urljoin(base_url, target).split("#", 1)[0]
            if url not in candidates:
                candidates.append(url)
    return candidates[:8]


class MirrorProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient, logger: logging.Logger | None = None):
        self.settings = settings
        self.client = client
        self.logger = logger or logging.getLogger(__name__)

    def log_failure(self, url: str, error: Exception) -> None:
        parsed = urlsplit(url)
        origin = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        status = error.response.status_code if isinstance(error, httpx.HTTPStatusError) else "n/a"
        chain = [
            {"type": type(item).__name__, "errno": getattr(item, "errno", None)}
            for item in exception_chain(error)
        ]
        self.logger.warning("Acquisition failed url=%s code=%s kind=%s status=%s causes=%s",
                            origin, failure_code(error), type(error).__name__, status, json.dumps(chain))

    def check_url(self, url: str) -> None:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https" or parsed.hostname not in self.settings.allowed_hosts
            or parsed.username or parsed.password or parsed.port not in {None, 443}
        ):
            raise RetrievalError("destination_not_allowed")

    async def fetch(self, url: str, referer: str | None = None, *, payload: dict | None = None) -> tuple[bytes, str]:
        for _ in range(6):
            self.check_url(url)
            headers = {"Referer": referer} if referer else {}
            async with self.client.stream("POST" if payload is not None else "GET", url,
                                          headers=headers, json=payload, follow_redirects=False) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    if payload is not None or not response.headers.get("location"):
                        raise RetrievalError("upstream_error")
                    url = urljoin(str(response.url), response.headers["location"])
                    continue
                response.raise_for_status()
                content = bytearray()
                limit = self.settings.max_pdf_bytes
                async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                    content.extend(chunk)
                    if len(content) >= 5 and not content.startswith(b"%PDF-"):
                        limit = min(limit, self.settings.max_html_bytes)
                    if len(content) > limit:
                        raise RetrievalError("response_too_large")
                return bytes(content), str(response.url)
        raise RetrievalError("upstream_error")

    async def fetch_verified(self, url: str, budget: list[int], referer: str | None = None) -> tuple[bytes, str]:
        content, landing = await self.fetch(url, referer)
        if content.startswith(b"%PDF-") or pdf_candidates(content, landing):
            return content, landing
        paths = verification_paths(content)
        if paths is not None and budget[0] > 0:
            budget[0] -= 1
            challenge_url, solution_url = (urljoin(landing, path) for path in paths)
            self.logger.warning("Verification required url=%s action=bounded_pow_v1", urlsplit(landing).path)
            try:
                raw, _ = await self.fetch(challenge_url, referer=landing)
                token = await asyncio.to_thread(solve_work, json.loads(raw))
                raw, _ = await self.fetch(solution_url, referer=landing, payload={"captcha": token})
                if json.loads(raw).get("success") is not True:
                    raise ValueError("verification_rejected")
            except (ValueError, TypeError, AttributeError) as error:
                self.logger.warning("Verification incomplete reason=%s", type(error).__name__)
                raise RetrievalError("verification_required") from None
            content, landing = await self.fetch(url, referer)
            self.logger.warning("Verification submitted accepted=true")
        if not content.startswith(b"%PDF-") and not pdf_candidates(content, landing) and is_verification_page(content):
            raise RetrievalError("verification_required")
        return content, landing

    async def retrieve(self, doi: str) -> Document:
        if not self.settings.provider_urls:
            raise RetrievalError("unconfigured")
        failures = []
        verification_budget = [1]
        for base in self.settings.provider_urls:
            try:
                content, landing = await self.fetch_verified(base + "/" + quote(doi, safe="/"), verification_budget)
                if content.startswith(b"%PDF-"):
                    pages = await asyncio.to_thread(validate_pdf, content)
                    return Document(content, landing, landing, pages)
                candidates = pdf_candidates(content, landing)
                if not candidates:
                    raise RetrievalError("no_pdf_link")
                for candidate in candidates:
                    try:
                        pdf, download = await self.fetch_verified(candidate, verification_budget, referer=landing)
                        pages = await asyncio.to_thread(validate_pdf, pdf)
                        return Document(pdf, landing, download, pages)
                    except (RetrievalError, httpx.HTTPError, ValueError) as error:
                        self.log_failure(candidate, error)
                        failures.append(failure_code(error))
                        continue
            except (RetrievalError, httpx.HTTPError, ValueError) as error:
                self.log_failure(base, error)
                failures.append(failure_code(error))
                continue
        for code in (
            "network_permission_denied", "verification_required", "rate_limited", "tls_failed",
            "connection_failed", "timeout", "access_denied", "upstream_error", "response_too_large",
            "destination_not_allowed", "invalid_document", "no_pdf_link", "not_found", "unavailable",
        ):
            if code in failures:
                raise RetrievalError(code)
        raise RetrievalError("unavailable")


def atomic_write(path: Path, content: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class PaperStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.papers = self.root / "papers"
        self.private = self.root / "private"
        for directory in (self.root, self.papers, self.private):
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    @staticmethod
    def paper_id(doi: str) -> str:
        return hashlib.sha256(doi.encode()).hexdigest()

    def lookup(self, paper_id: str) -> tuple[PaperResult, bytes] | None:
        if re.fullmatch(r"[0-9a-f]{64}", paper_id) is None:
            return None
        path = self.papers / (paper_id + ".pdf")
        record = self.private / (paper_id + ".json")
        try:
            metadata = json.loads(record.read_text())
            public = PaperResult.model_validate(metadata["paper"])
            content = path.read_bytes()
            if (
                public.paper_id != paper_id
                or self.paper_id(public.doi) != paper_id
                or public.sha256 != hashlib.sha256(content).hexdigest()
                or public.size_bytes != len(content)
            ):
                return None
            return public.model_copy(update={"cached": True, "file_path": str(path)}), content
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save(self, doi: str, document: Document) -> PaperResult:
        paper_id = self.paper_id(doi)
        path = self.papers / (paper_id + ".pdf")
        result = PaperResult(
            doi=doi, paper_id=paper_id, file_path=str(path),
            resource_uri=f"papers://{paper_id}/pdf",
            size_bytes=len(document.content), sha256=hashlib.sha256(document.content).hexdigest(),
            page_count=document.page_count, cached=False,
        )
        def without_query(url: str) -> str:
            parsed = urlsplit(url)
            return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

        record = {
            "paper": result.model_dump(),
            "acquisition": {
                "landing_url": without_query(document.landing_url),
                "download_url": without_query(document.download_url),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "identity_verification": "not_checked",
            },
        }
        atomic_write(path, document.content)
        atomic_write(self.private / (paper_id + ".json"), json.dumps(record, indent=2).encode())
        return result


class PaperService:
    def __init__(self, settings: Settings, provider: MirrorProvider, store: PaperStore, logger: logging.Logger | None = None):
        self.settings = settings
        self.provider = provider
        self.store = store
        self.logger = logger or logging.getLogger(__name__)
        self.lock = asyncio.Lock()

    async def retrieve(self, doi: str) -> PaperResult:
        doi = normalize_doi(doi)
        try:
            async with asyncio.timeout(self.settings.retrieval_timeout):
                async with self.lock:
                    existing = await asyncio.to_thread(self.store.lookup, self.store.paper_id(doi))
                    if existing is not None:
                        return existing[0]
                    document = await self.provider.retrieve(doi)
                    return await asyncio.to_thread(self.store.save, doi, document)
        except TimeoutError:
            raise RetrievalError("timeout") from None


def make_http_client(settings: Settings) -> httpx.AsyncClient:
    context = ssl.create_default_context()
    transport = HostRoutingTransport(settings.host_overrides, context) if settings.host_overrides else None
    return httpx.AsyncClient(
        timeout=settings.request_timeout,
        proxy=settings.proxy_url,
        verify=context,
        transport=transport,
        headers={"User-Agent": "PaperRetrievalMCP/0.1", "Accept": "text/html,application/pdf"},
        limits=httpx.Limits(max_connections=2, max_keepalive_connections=2),
    )
