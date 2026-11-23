"""Validate an actual download through a separate stdio MCP process."""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from pypdf import PdfReader

from paper_retrieval.core import Settings, atomic_write, make_http_client, normalize_doi


def normalized_text(value: str) -> str:
    return "".join(char.lower() for char in unicodedata.normalize("NFKD", value) if char.isalnum())


async def validate(arguments: argparse.Namespace) -> int:
    started = datetime.now(timezone.utc)
    project = Path(__file__).resolve().parents[1]
    directory = arguments.data_dir or project / ".data" / ("live-" + started.strftime("%Y%m%dT%H%M%S.%fZ"))
    directory = directory.resolve()
    (directory / "private").mkdir(parents=True, exist_ok=True, mode=0o700)
    settings = Settings(
        provider_urls=tuple(arguments.provider_url), extra_hosts=tuple(arguments.allow_host),
        proxy_url=arguments.proxy_url, data_dir=directory,
        request_timeout=arguments.request_timeout, retrieval_timeout=arguments.timeout,
        host_overrides=dict(item.split("=", 1) for item in arguments.resolve),
    )
    doi = normalize_doi(arguments.doi)
    metadata_url = "https://api.crossref.org/works/" + quote(doi, safe="/")
    report = {
        "started_at_utc": started.isoformat(), "doi": doi, "transport": "stdio",
        "provider_urls": list(settings.provider_urls), "proxy_enabled": bool(settings.proxy_url),
        "host_overrides": settings.host_overrides,
        "status": "failed", "checks": {},
    }
    try:
        async with make_http_client(settings) as http:
            async with asyncio.timeout(15):
                response = await http.get(metadata_url)
                response.raise_for_status()
                metadata = response.json()["message"]
                report["crossref"] = {
                    "url": metadata_url, "doi": metadata.get("DOI"),
                    "titles": metadata.get("title", []), "licenses": metadata.get("license", []),
                }
    except Exception as error:
        report["metadata_error"] = type(error).__name__

    environment = {
        key: os.environ[key] for key in (
            "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY",
            "https_proxy", "http_proxy", "all_proxy", "no_proxy",
        ) if key in os.environ
    }
    environment.update({
        "PAPER_PROVIDER_URLS": ",".join(settings.provider_urls),
        "PAPER_ALLOWED_HOSTS": ",".join(settings.extra_hosts),
        "PAPER_DATA_DIR": str(directory),
        "PAPER_REQUEST_TIMEOUT": str(settings.request_timeout),
        "PAPER_RETRIEVAL_TIMEOUT": str(settings.retrieval_timeout),
        "PAPER_PROXY_URL": settings.proxy_url or "",
        "PAPER_HOST_OVERRIDES": json.dumps(settings.host_overrides),
    })
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "paper_retrieval.server"], env=environment,
    )
    try:
        async with asyncio.timeout(settings.retrieval_timeout + 30):
            async with Client(parameters) as client:
                tools = (await client.list_tools()).tools
                report["checks"]["tool_discovery"] = any(tool.name == "retrieve_paper" for tool in tools)
                result = await client.call_tool("retrieve_paper", {"doi": doi})
                if result.is_error:
                    report["tool_error"] = [item.text for item in result.content if hasattr(item, "text")]
                else:
                    public = result.structured_content
                    report["paper"] = public
                    record = json.loads((directory / "private" / (public["paper_id"] + ".json")).read_text())
                    report["acquisition"] = record["acquisition"]
                    surface = json.dumps([tool.model_dump(mode="json") for tool in tools]) + result.model_dump_json()
                    private_hosts = [urlsplit(url).hostname for url in settings.provider_urls if urlsplit(url).hostname != "doi.org"]
                    report["checks"]["provider_hosts_absent_from_tool_surface"] = all(host not in surface for host in private_hosts)
                    report["checks"]["fresh_download"] = public["cached"] is False
                    content = Path(public["file_path"]).read_bytes()
                    report["checks"]["file_size_matches"] = len(content) == public["size_bytes"]
                    report["checks"]["file_sha256_matches"] = hashlib.sha256(content).hexdigest() == public["sha256"]
                    reader = PdfReader(public["file_path"], strict=True)
                    report["checks"]["page_count_matches"] = len(reader.pages) == public["page_count"] > 0
                    text = "\n".join(page.extract_text() or "" for page in reader.pages[:3])
                    report["checks"]["doi_found_in_first_three_pages"] = doi in re.sub(r"\s+", "", text).lower()
                    titles = report.get("crossref", {}).get("titles", [])
                    report["checks"]["crossref_title_found_in_first_three_pages"] = bool(titles) and any(
                        normalized_text(title) in normalized_text(text) for title in titles
                    )
                    resource = await client.read_resource(public["resource_uri"])
                    resource_pdf = base64.b64decode(resource.contents[0].blob)
                    report["checks"]["resource_bytes_match_file"] = resource_pdf == content
                    repeated = await client.call_tool("retrieve_paper", {"doi": doi})
                    report["checks"]["second_call_uses_cache"] = not repeated.is_error and repeated.structured_content["cached"] is True
                    if all(report["checks"].values()):
                        report["status"] = "passed"
    except Exception as error:
        report["validation_error"] = type(error).__name__
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    path = directory / "private" / "live-validation.json"
    report["report_path"] = str(path)
    atomic_write(path, json.dumps(report, ensure_ascii=False, indent=2).encode())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doi", required=True)
    parser.add_argument("--provider-url", action="append", required=True)
    parser.add_argument("--allow-host", action="append", default=[])
    parser.add_argument("--proxy-url")
    parser.add_argument("--resolve", action="append", default=[], metavar="HOST=IP")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--request-timeout", type=float, default=15)
    parser.add_argument("--timeout", type=float, default=90)
    raise SystemExit(asyncio.run(validate(parser.parse_args())))


if __name__ == "__main__":
    main()
