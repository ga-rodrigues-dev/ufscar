"""Local stdio MCP server. Provider information stays in operator records."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ResourceError, ResourceNotFoundError, ToolError

from .core import (
    MESSAGES, MirrorProvider, PaperResult, PaperService, PaperStore,
    RetrievalError, Settings, make_http_client,
)


def create_server(settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None) -> MCPServer:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(server: MCPServer) -> AsyncIterator[PaperService]:
        store = PaperStore(settings.data_dir)
        handler = RotatingFileHandler(store.private / "errors.log", maxBytes=1024 * 1024, backupCount=2)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger = logging.getLogger(f"paper_retrieval.{id(server)}")
        logger.propagate = False
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        try:
            client = make_http_client(settings) if transport is None else httpx.AsyncClient(transport=transport)
            async with client:
                service = PaperService(settings, MirrorProvider(settings, client, logger), store, logger)
                yield service
        finally:
            logger.removeHandler(handler)
            handler.close()

    server = MCPServer(
        "Scientific Papers", version="0.1.0", lifespan=lifespan, log_level="WARNING",
        instructions="Retrieve scientific paper PDFs by DOI. Access a retrieved PDF using its resource URI or local file path.",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    @server.tool()
    async def retrieve_paper(doi: str, ctx: Context[PaperService]) -> PaperResult:
        """Retrieve a scientific paper PDF by DOI or https://doi.org/ URL.

        Returns its local path, PDF resource URI, page count and SHA-256 checksum.
        Reuses an intact local copy when available. File retrieval does not verify
        that the document's contents match the requested article.
        """
        service = ctx.request_context.lifespan_context
        try:
            return await service.retrieve(doi)
        except RetrievalError as error:
            raise ToolError(str(error)) from None
        except Exception:
            service.logger.exception("Paper retrieval failed")
            raise ToolError(MESSAGES["internal"]) from None

    @server.resource("papers://{paper_id}/pdf", mime_type="application/pdf")
    async def paper_pdf(paper_id: str, ctx: Context[PaperService]) -> bytes:
        """Read a previously retrieved scientific paper PDF from the local collection."""
        service = ctx.request_context.lifespan_context
        try:
            stored = await asyncio.to_thread(service.store.lookup, paper_id)
        except Exception:
            service.logger.exception("Reading the local PDF failed")
            raise ResourceError(MESSAGES["internal"]) from None
        if stored is None:
            raise ResourceNotFoundError(MESSAGES["missing"])
        return stored[1]

    return server


def main() -> None:
    try:
        server = create_server()
    except (ValueError, OSError):
        raise SystemExit("Invalid paper retrieval configuration. Check the operator settings.") from None
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
