"""Per-client host routing that preserves the original HTTP and TLS hostname."""

from collections.abc import AsyncIterable, AsyncIterator, Iterator, Mapping
from contextlib import contextmanager
import ssl

import httpcore
import httpx


@contextmanager
def translate_errors() -> Iterator[None]:
    try:
        yield
    except (
        httpcore.TimeoutException, httpcore.NetworkError, httpcore.ProtocolError,
        httpcore.ProxyError, httpcore.UnsupportedProtocol,
    ) as error:
        exception = getattr(httpx, type(error).__name__, httpx.TransportError)
        raise exception(str(error)) from error


class HostRoutingBackend(httpcore.AnyIOBackend):
    def __init__(self, overrides: Mapping[str, str]):
        self.overrides = dict(overrides)

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        return await super().connect_tcp(
            self.overrides.get(host, host), port, timeout=timeout,
            local_address=local_address, socket_options=socket_options,
        )


class ResponseStream(httpx.AsyncByteStream):
    def __init__(self, stream: AsyncIterable[bytes]):
        self.stream = stream

    async def __aiter__(self) -> AsyncIterator[bytes]:
        with translate_errors():
            async for chunk in self.stream:
                yield chunk

    async def aclose(self) -> None:
        await self.stream.aclose()


class HostRoutingTransport(httpx.AsyncBaseTransport):
    def __init__(self, overrides: Mapping[str, str], context: ssl.SSLContext):
        self.pool = httpcore.AsyncConnectionPool(
            ssl_context=context, max_connections=2, max_keepalive_connections=2,
            network_backend=HostRoutingBackend(overrides),
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # Only connect_tcp changes the socket destination. The pool still sees
        # the original URL, uses that hostname for SNI, and verifies its certificate.
        outgoing = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme, host=request.url.raw_host,
                port=request.url.port, target=request.url.raw_path,
            ),
            headers=request.headers.raw, content=request.stream, extensions=request.extensions,
        )
        with translate_errors():
            response = await self.pool.handle_async_request(outgoing)
        return httpx.Response(
            response.status, headers=response.headers,
            stream=ResponseStream(response.stream), extensions=response.extensions,
        )

    async def aclose(self) -> None:
        await self.pool.aclose()
