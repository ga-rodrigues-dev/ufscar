"""Offline behavior and MCP contract checks with synthetic documents."""

import asyncio
import base64
import hashlib
import io
import json
import logging
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import httpx
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from pypdf import PdfWriter

from paper_retrieval.core import (
    Document, MirrorProvider, PaperService, PaperStore, RetrievalError,
    Settings, make_http_client, normalize_doi, pdf_candidates,
)
from paper_retrieval.server import create_server


DOI = "10.1234/test.paper"
ORIGIN = "https://sci-hub.provider.example"


def make_pdf() -> bytes:
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(buffer)
    return buffer.getvalue()


class InputTests(unittest.TestCase):
    def test_doi_normalization(self):
        for value in (" DOI:10.1234/Test.Paper ", "https://doi.org/10.1234%2FTest.Paper", DOI):
            self.assertEqual(normalize_doi(value), DOI)

    def test_invalid_inputs(self):
        for value in ("a paper title", "https://evil.example/10.1234/test", "10.1234/a\nb", "http://doi.org/10.1234/a"):
            with self.subTest(value=value), self.assertRaises(RetrievalError):
                normalize_doi(value)

    def test_unsafe_configuration(self):
        for value in ("http://mirror.example", "https://user:secret@mirror.example", "https://127.0.0.1", "https://mirror.example:8080"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Settings(provider_urls=(value,))
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Settings(request_timeout=value)

    def test_pdf_link_variants(self):
        html = b'<iframe src="//cdn.provider.example/a.pdf#view=FitH"></iframe><object data="/b.pdf"></object><a href="/c.pdf?download=1">Download</a>'
        self.assertEqual(pdf_candidates(html, ORIGIN + "/article"), [
            "https://cdn.provider.example/a.pdf", ORIGIN + "/b.pdf", ORIGIN + "/c.pdf?download=1",
        ])

    def test_publisher_citation_metadata_and_pdf_mime_links(self):
        html = b'<meta name="citation_pdf_url" content="/article/file?id=10.1234/paper&amp;type=printable"><link type="application/pdf" href="/alternate"><a type="application/pdf" href="/download?id=1">PDF</a>'
        self.assertEqual(pdf_candidates(html, ORIGIN), [
            ORIGIN + "/article/file?id=10.1234/paper&type=printable",
            ORIGIN + "/alternate", ORIGIN + "/download?id=1",
        ])

    def test_proxy_settings_do_not_expose_credentials_in_repr_or_errors(self):
        proxy = "socks5h://user:secret@127.0.0.1:1080"
        self.assertNotIn("secret", repr(Settings(proxy_url=proxy)))
        for value in ("ftp://127.0.0.1:1080", "https://user:secret@", "socks5h://127.0.0.1:0", "http://127.0.0.1:99999"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "^Invalid proxy configuration\\.$"):
                Settings(proxy_url=value)


class RetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.settings = Settings(provider_urls=(ORIGIN,), data_dir=Path(self.temporary.name))
        self.pdf = make_pdf()
        self.requests = []
        self.logger = logging.getLogger(f"test.retrieval.{id(self)}")
        self.logger.addHandler(logging.NullHandler())
        self.logger.propagate = False

    async def run_service(self, handler, action, settings=None):
        settings = settings or self.settings
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            store = PaperStore(settings.data_dir)
            service = PaperService(settings, MirrorProvider(settings, client, self.logger), store)
            await action(service)

    async def test_download_cache_resource_and_private_provenance(self):
        def handler(request):
            self.requests.append(str(request.url))
            if request.url.path == "/" + DOI:
                return httpx.Response(200, text='<iframe id="pdf" src="/files/paper.pdf"></iframe>')
            self.assertEqual(request.headers["referer"], ORIGIN + "/" + DOI)
            return httpx.Response(200, content=self.pdf)

        server = create_server(self.settings, httpx.MockTransport(handler))
        async with Client(server, raise_exceptions=True) as client:
            tools = (await client.list_tools()).tools
            wire = json.dumps([tool.model_dump(mode="json") for tool in tools])
            self.assertNotIn("sci-hub", wire)
            self.assertNotIn("provider.example", wire)
            self.assertEqual([tool.name for tool in tools], ["retrieve_paper"])
            first = await client.call_tool("retrieve_paper", {"doi": DOI})
            self.assertFalse(first.is_error, str(first))
            public = first.structured_content
            self.assertEqual(public["sha256"], hashlib.sha256(self.pdf).hexdigest())
            self.assertEqual(public["page_count"], 1)
            self.assertEqual(public["doi"], DOI)
            self.assertFalse(public["cached"])
            self.assertEqual(Path(public["file_path"]).read_bytes(), self.pdf)
            self.assertNotIn("provider.example", first.model_dump_json())
            self.assertNotIn("sci-hub", first.model_dump_json())
            second = await client.call_tool("retrieve_paper", {"doi": DOI.upper()})
            self.assertTrue(second.structured_content["cached"])
            self.assertEqual(len(self.requests), 2)
            resource = await client.read_resource(public["resource_uri"])
            self.assertEqual(base64.b64decode(resource.contents[0].blob), self.pdf)
            record = json.loads((self.settings.data_dir / "private" / (public["paper_id"] + ".json")).read_text())
            self.assertEqual(record["acquisition"]["download_url"], ORIGIN + "/files/paper.pdf")
            self.assertEqual(record["acquisition"]["identity_verification"], "not_checked")

    async def test_failed_network_does_not_reveal_provider(self):
        def handler(request):
            raise httpx.ConnectError("Cannot connect to " + ORIGIN, request=request)
        server = create_server(self.settings, httpx.MockTransport(handler))
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool("retrieve_paper", {"doi": DOI})
            self.assertTrue(result.is_error)
            self.assertNotIn("sci-hub", result.model_dump_json())
            self.assertNotIn("provider.example", result.model_dump_json())
            self.assertIn("connection could not be established", result.content[0].text)
        logs = (self.settings.data_dir / "private" / "errors.log").read_text()
        self.assertIn(ORIGIN, logs)

    async def test_unexpected_exception_is_sanitized(self):
        server = create_server(self.settings, httpx.MockTransport(lambda request: httpx.Response(200, content=self.pdf)))
        with patch.object(PaperStore, "save", side_effect=OSError("Private origin: " + ORIGIN)):
            async with Client(server, raise_exceptions=True) as client:
                result = await client.call_tool("retrieve_paper", {"doi": DOI})
                self.assertTrue(result.is_error)
                self.assertNotIn(ORIGIN, result.model_dump_json())
                self.assertIn("Contact the server operator", result.content[0].text)

    async def test_mirror_fallback_after_bad_pdf(self):
        second = "https://second.provider.example"
        settings = replace(self.settings, provider_urls=(ORIGIN, second))
        def handler(request):
            self.requests.append(str(request.url))
            content = b"%PDF-1.7\nThis is not a PDF" if request.url.host == "sci-hub.provider.example" else self.pdf
            return httpx.Response(200, content=content, headers={"content-type": "application/pdf"})
        async def action(service):
            result = await service.retrieve(DOI)
            self.assertEqual(result.sha256, hashlib.sha256(self.pdf).hexdigest())
            self.assertEqual(len(self.requests), 2)
        await self.run_service(handler, action, settings)

    async def test_disallowed_redirect_is_not_followed(self):
        def handler(request):
            self.requests.append(str(request.url))
            return httpx.Response(302, headers={"location": "https://127.0.0.1/secrets"})
        async def action(service):
            with self.assertRaises(RetrievalError):
                await service.retrieve(DOI)
            self.assertEqual(len(self.requests), 1)
        await self.run_service(handler, action)

    async def test_extra_cdn_host_requires_configuration(self):
        def handler(request):
            self.requests.append(str(request.url))
            if request.url.host == "cdn.provider.example":
                return httpx.Response(200, content=self.pdf)
            return httpx.Response(200, text='<embed src="https://cdn.provider.example/a.pdf">')
        async def denied(service):
            with self.assertRaises(RetrievalError):
                await service.retrieve(DOI)
            self.assertEqual(len(self.requests), 1)
        await self.run_service(handler, denied)
        async def permitted(service):
            self.assertEqual((await service.retrieve(DOI)).page_count, 1)
        await self.run_service(handler, permitted, replace(self.settings, extra_hosts=("cdn.provider.example",)))

    async def test_wrong_content_type_does_not_override_signature(self):
        async def action(service):
            with self.assertRaises(RetrievalError):
                await service.retrieve(DOI)
            self.assertFalse(list(service.store.papers.iterdir()))
        await self.run_service(lambda request: httpx.Response(200, content=b"<html>Blocked</html>", headers={"content-type": "application/pdf"}), action)

    async def test_size_limit(self):
        async def action(service):
            with self.assertRaises(RetrievalError):
                await service.retrieve(DOI)
            self.assertFalse(list(service.store.papers.iterdir()))
        await self.run_service(lambda request: httpx.Response(200, content=self.pdf), action, replace(self.settings, max_pdf_bytes=10))

    async def test_html_limit_and_redirect_loop_are_bounded(self):
        async def action(service):
            with self.assertRaises(RetrievalError):
                await service.retrieve(DOI)
        await self.run_service(lambda request: httpx.Response(200, content=b"<html>" * 100), action, replace(self.settings, max_html_bytes=50))
        def loop(request):
            self.requests.append(str(request.url))
            return httpx.Response(302, headers={"location": "/again"})
        await self.run_service(loop, action)
        self.assertEqual(len(self.requests), 6)

    async def test_total_timeout(self):
        async def handler(request):
            await asyncio.sleep(1)
            return httpx.Response(200, content=self.pdf)
        async def action(service):
            with self.assertRaises(RetrievalError) as raised:
                await service.retrieve(DOI)
            self.assertEqual(raised.exception.code, "timeout")
        await self.run_service(handler, action, replace(self.settings, retrieval_timeout=0.05))

    async def test_modified_cache_is_downloaded_again(self):
        def handler(request):
            self.requests.append(str(request.url))
            return httpx.Response(200, content=self.pdf)
        async def action(service):
            first = await service.retrieve(DOI)
            Path(first.file_path).write_bytes(b"broken")
            second = await service.retrieve(DOI)
            self.assertFalse(second.cached)
            self.assertEqual(Path(second.file_path).read_bytes(), self.pdf)
            self.assertEqual(len(self.requests), 2)
            self.assertIsNone(service.store.lookup("../../private/anything"))
        await self.run_service(handler, action)

    async def test_concurrent_duplicate_requests_share_download(self):
        async def handler(request):
            self.requests.append(str(request.url))
            await asyncio.sleep(0.01)
            return httpx.Response(200, content=self.pdf)
        async def action(service):
            results = await asyncio.gather(service.retrieve(DOI), service.retrieve(DOI))
            self.assertEqual(len(self.requests), 1)
            self.assertEqual([result.cached for result in results], [False, True])
        await self.run_service(handler, action)

    async def test_unconfigured_server_has_actionable_error(self):
        server = create_server(replace(self.settings, provider_urls=()))
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool("retrieve_paper", {"doi": DOI})
            self.assertTrue(result.is_error)
            self.assertIn("not configured", result.content[0].text)

    async def test_socks_proxy_receives_the_destination_hostname(self):
        destinations = []
        completed = asyncio.Event()
        async def socks_server(reader, writer):
            try:
                version, count = await reader.readexactly(2)
                self.assertEqual(version, 5)
                await reader.readexactly(count)
                writer.write(b"\x05\x00")
                await writer.drain()
                command = await reader.readexactly(4)
                self.assertEqual(command, b"\x05\x01\x00\x03")
                count = (await reader.readexactly(1))[0]
                hostname = (await reader.readexactly(count)).decode()
                port = int.from_bytes(await reader.readexactly(2), "big")
                destinations.append((hostname, port))
                writer.write(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00")
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
                completed.set()
        listener = await asyncio.start_server(socks_server, "127.0.0.1", 0)
        async with listener:
            port = listener.sockets[0].getsockname()[1]
            settings = replace(self.settings, proxy_url=f"socks5h://127.0.0.1:{port}")
            async with make_http_client(settings) as client:
                with self.assertRaises(httpx.ProxyError):
                    await client.get("https://only-the-proxy-can-resolve.invalid/paper")
            await asyncio.wait_for(completed.wait(), 2)
        self.assertEqual(destinations, [("only-the-proxy-can-resolve.invalid", 443)])

    async def test_legacy_protocol_errors_are_also_sanitized(self):
        def handler(request):
            raise httpx.ConnectError(ORIGIN, request=request)
        server = create_server(self.settings, httpx.MockTransport(handler))
        async with Client(server, mode="legacy") as client:
            result = await client.call_tool("retrieve_paper", {"doi": DOI})
            self.assertTrue(result.is_error)
            self.assertNotIn(ORIGIN, result.model_dump_json())

    async def test_stdio_subprocess_serves_a_cached_pdf(self):
        store = PaperStore(self.settings.data_dir)
        store.save(DOI, Document(self.pdf, ORIGIN, ORIGIN, 1))
        parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "paper_retrieval.server"],
            env={"PAPER_DATA_DIR": str(self.settings.data_dir), "PAPER_PROVIDER_URLS": ""},
        )
        async with asyncio.timeout(15):
            async with Client(parameters) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual([tool.name for tool in tools], ["retrieve_paper"])
                result = await client.call_tool("retrieve_paper", {"doi": DOI})
                self.assertFalse(result.is_error)
                self.assertTrue(result.structured_content["cached"])
                self.assertEqual(result.structured_content["sha256"], hashlib.sha256(self.pdf).hexdigest())
                self.assertNotIn(ORIGIN, result.model_dump_json())


if __name__ == "__main__":
    unittest.main()
