"""JSON command line interface for scientific paper retrieval."""

import argparse
import asyncio
from dataclasses import replace
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from .core import (
    MESSAGES, MirrorProvider, PaperService, PaperStore, RetrievalError,
    Settings, make_http_client,
)
from .pdf_export import export_clean_pdf


def load_settings(path: Path, data_dir: Path | None) -> Settings:
    settings = Settings.from_env()
    if path.exists():
        values = json.loads(path.read_text())
        if not isinstance(values, dict):
            raise ValueError("Invalid configuration")
        if "provider_urls" in values:
            values["provider_urls"] = tuple(values["provider_urls"])
        if "extra_hosts" in values:
            values["extra_hosts"] = tuple(values["extra_hosts"])
        if "data_dir" in values:
            values["data_dir"] = Path(values["data_dir"]).expanduser().resolve()
        settings = replace(settings, **values)
    if data_dir is not None:
        settings = replace(settings, data_dir=data_dir.expanduser().resolve())
    return settings


async def retrieve(settings: Settings, doi: str, output: Path | None) -> dict:
    store = PaperStore(settings.data_dir)
    logger = logging.getLogger("paper_retrieval.cli")
    logger.propagate = False
    handler = RotatingFileHandler(store.private / "cli-errors.log", maxBytes=1048576, backupCount=2)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        async with make_http_client(settings) as client:
            service = PaperService(settings, MirrorProvider(settings, client, logger), store, logger)
            result = await service.retrieve(doi)
        public = await asyncio.to_thread(export_clean_pdf, store, result, output)
        return {"ok": True, **public}
    except (RetrievalError, FileExistsError):
        raise
    except Exception:
        logger.exception("Retrieval failed")
        raise RetrievalError("internal") from None
    finally:
        logger.removeHandler(handler)
        handler.close()


def main() -> None:
    default_config = Settings().data_dir / "private" / "settings.json"
    parser = argparse.ArgumentParser(prog="papers", description="Retrieve scientific paper PDFs by DOI.")
    parser.add_argument("--config", type=Path, help="Operator configuration file.")
    parser.add_argument("--data-dir", type=Path, help="Local collection directory.")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("retrieve", help="Retrieve a paper, export a metadata-cleaned PDF and print JSON.")
    download.add_argument("doi", help="DOI or https://doi.org/ URL.")
    download.add_argument("--output", type=Path, help="Copy the PDF to a new file; existing files are preserved.")
    arguments = parser.parse_args()
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    try:
        if arguments.config is not None and not arguments.config.is_file():
            raise ValueError("Missing configuration")
        settings = load_settings(arguments.config or default_config, arguments.data_dir)
    except (ValueError, TypeError, OSError):
        print(json.dumps({"ok": False, "error": {"code": "configuration", "message": "Invalid or unreadable operator configuration."}}))
        raise SystemExit(2) from None
    try:
        result = asyncio.run(retrieve(settings, arguments.doi, arguments.output))
    except FileExistsError:
        result = {"ok": False, "error": {"code": "output_exists", "message": "The output file already exists. Choose another path."}}
    except RetrievalError as error:
        result = {"ok": False, "error": {"code": error.code, "message": str(error)}}
    except Exception:
        result = {"ok": False, "error": {"code": "internal", "message": MESSAGES["internal"]}}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
