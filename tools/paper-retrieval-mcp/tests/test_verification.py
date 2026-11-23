import asyncio
import base64
import errno
import hashlib
import io
import json
import logging
from pathlib import Path
import tempfile
import unittest

import httpx
from pypdf import PdfWriter

from paper_retrieval.core import MirrorProvider, RetrievalError, Settings
from paper_retrieval.verification import solve_work, verification_paths


HOST = "https://private-provider.example"
DOI = "10.1234/verification"
GATE = b'''<title>Verification</title><altcha-widget challengeurl="/captcha/challenge/123"></altcha-widget>
<script>fetch('/captcha/solution/123', {method:'POST'})</script>'''


def challenge(number=42):
    return {
        "algorithm": "SHA-256", "salt": "test-salt", "signature": "opaque-test-signature",
        "challenge": hashlib.sha256(("test-salt" + str(number)).encode()).hexdigest(), "maxNumber": 100,
    }


class WorkTests(unittest.TestCase):
    def test_solution_matches_server_work_and_preserves_signature(self):
        value = json.loads(base64.b64decode(solve_work(challenge())))
        self.assertEqual(value["number"], 42)
        self.assertEqual(value["signature"], challenge()["signature"])
        self.assertEqual(hashlib.sha256((value["salt"] + str(value["number"])).encode()).hexdigest(), value["challenge"])

    def test_work_is_bounded_and_unrecognized_challenges_rejected(self):
        for data in (
            {**challenge(), "maxNumber": 2_000_001},
            {**challenge(), "algorithm": "unknown"},
            {**challenge(), "salt": "a" * 513},
            {**challenge(), "maxNumber": True},
            {**challenge(), "challenge": "not-a-hash"},
            {**challenge(), "maxNumber": 1},
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                solve_work(data)
        with self.assertRaises(ValueError):
            solve_work(challenge(), max_seconds=0)

    def test_a_report_form_is_not_an_access_gate(self):
        self.assertIsNone(verification_paths(b'<altcha-widget challengeurl="/captcha/challenge"></altcha-widget>'))
        self.assertIsNone(verification_paths(b'<altcha-widget challengeurl="https://evil.example/captcha/challenge/123"></altcha-widget>'))
        self.assertIsNone(verification_paths(GATE.replace(b"/captcha/solution/123", b"/send-message")))
        self.assertEqual(verification_paths(GATE), ("/captcha/challenge/123", "/captcha/solution/123"))


class FailureAndVerificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.settings = Settings(provider_urls=(HOST,), data_dir=Path(self.temporary.name))
        self.logger = logging.getLogger(f"test.verification.{id(self)}")
        self.logger.addHandler(logging.NullHandler())
        self.logger.propagate = False
        buffer = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(buffer)
        self.pdf = buffer.getvalue()

    async def expect_failure(self, handler, code):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(RetrievalError) as caught:
                await MirrorProvider(self.settings, client, self.logger).retrieve(DOI)
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn("private-provider", str(caught.exception))

    async def test_permission_failure_survives_nested_network_wrappers(self):
        def handler(request):
            try:
                raise PermissionError(errno.EPERM, "Network forbidden")
            except PermissionError as cause:
                raise httpx.ConnectError("All connection attempts failed", request=request) from cause
        await self.expect_failure(handler, "network_permission_denied")

    async def test_connection_failure_is_not_article_unavailability(self):
        def handler(request):
            raise httpx.ConnectError("Cannot connect to " + HOST, request=request)
        await self.expect_failure(handler, "connection_failed")

    async def test_http_status_and_missing_link_failures_are_distinct(self):
        for status, code in ((403, "access_denied"), (404, "not_found"), (429, "rate_limited"), (503, "upstream_error")):
            with self.subTest(status=status):
                await self.expect_failure(lambda request: httpx.Response(status), code)
        await self.expect_failure(lambda request: httpx.Response(200, text="<title>Article</title>"), "no_pdf_link")
        await self.expect_failure(lambda request: httpx.Response(200, text='<title>Checking your browser</title>'), "verification_required")

    async def test_verification_cookie_allows_pdf_in_the_same_client(self):
        requests = []
        def handler(request):
            requests.append((request.method, request.url.path))
            if request.url.path == "/captcha/challenge/123":
                return httpx.Response(200, json=challenge())
            if request.url.path == "/captcha/solution/123":
                self.assertEqual(request.method, "POST")
                body = json.loads(request.content)
                value = json.loads(base64.b64decode(body["captcha"]))
                self.assertEqual(value["number"], 42)
                return httpx.Response(200, json={"success": True}, headers={"set-cookie": "test_access=yes; Path=/"})
            if "test_access=yes" not in request.headers.get("cookie", ""):
                return httpx.Response(200, content=GATE)
            if request.url.path.endswith(".pdf"):
                return httpx.Response(200, content=self.pdf)
            return httpx.Response(200, text='<iframe src="/paper.pdf"></iframe>')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            document = await MirrorProvider(self.settings, client, self.logger).retrieve(DOI)
            self.assertEqual(document.content, self.pdf)
            self.assertEqual(document.download_url, HOST + "/paper.pdf")
            self.assertEqual(requests.count(("POST", "/captcha/solution/123")), 1)

    async def test_repeated_gate_does_not_repeat_work_or_submission(self):
        submissions = []
        def handler(request):
            if request.url.path == "/captcha/challenge/123":
                return httpx.Response(200, json=challenge())
            if request.method == "POST":
                submissions.append(request.url.path)
                return httpx.Response(200, json={"success": True})
            return httpx.Response(200, content=GATE)
        await self.expect_failure(handler, "verification_required")
        self.assertEqual(submissions, ["/captcha/solution/123"])


if __name__ == "__main__":
    unittest.main()
