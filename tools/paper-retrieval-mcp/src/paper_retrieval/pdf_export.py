"""Export a derived PDF without document information or XMP metadata."""

import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

from .core import PaperResult, PaperStore, atomic_write


def clean_metadata(content: bytes) -> bytes:
    reader = PdfReader(io.BytesIO(content), strict=False)
    if reader.is_encrypted:
        raise ValueError("Encrypted document")
    page_count = len(reader.pages)
    reader.trailer.pop("/Info", None)
    pending = [reader.root_object]
    seen = set()
    while pending:
        obj = pending.pop()
        if isinstance(obj, IndirectObject):
            obj = obj.get_object()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        if isinstance(obj, DictionaryObject):
            obj.pop("/Metadata", None)
            pending.extend(obj.values())
        elif isinstance(obj, ArrayObject):
            pending.extend(obj)
    writer = PdfWriter(clone_from=reader)
    writer.metadata = None
    # pypdf 7 copies the original trailer IDs; do not retain those identifiers.
    writer._ID = None
    writer.compress_identical_objects(remove_duplicates=False, remove_unreferenced=True)
    target = io.BytesIO()
    writer.write(target)
    result = target.getvalue()
    checked = PdfReader(io.BytesIO(result), strict=True)
    if checked.metadata is not None or checked.xmp_metadata is not None or len(checked.pages) != page_count:
        raise ValueError("Export validation failed")
    return result


def export_clean_pdf(store: PaperStore, paper: PaperResult, destination: Path | None) -> dict:
    original = Path(paper.file_path).read_bytes()
    if hashlib.sha256(original).hexdigest() != paper.sha256:
        raise ValueError("Original integrity check failed")
    cleaned = clean_metadata(original)
    exports = store.root / "exports"
    exports.mkdir(exist_ok=True, mode=0o700)
    explicit = destination is not None
    path = destination.expanduser().resolve() if explicit else exports / (paper.paper_id + ".pdf")
    if path == Path(paper.file_path).resolve():
        raise FileExistsError
    record = {
        "operation": "remove_pdf_metadata", "created_at": datetime.now(timezone.utc).isoformat(),
        "original": {"path": paper.file_path, "sha256": paper.sha256},
        "export": {"path": str(path), "sha256": hashlib.sha256(cleaned).hexdigest(), "size_bytes": len(cleaned)},
        "removed": ["document_info", "xmp_metadata", "trailer_identifiers"],
    }
    # Record the transformation before publishing its output. Failed publication
    # remains explicitly distinguishable from a completed export.
    receipt = store.private / ("export-" + uuid4().hex + ".json")
    record["status"] = "pending"
    atomic_write(receipt, json.dumps(record, indent=2).encode())
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(cleaned)
            stream.flush()
            os.fsync(stream.fileno())
        if explicit:
            os.link(temporary, path)  # Atomic publication without overwriting.
        else:
            temporary.replace(path)
        record["status"] = "complete"
        atomic_write(receipt, json.dumps(record, indent=2).encode())
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {
        **paper.model_dump(exclude={"resource_uri"}), "file_path": str(path),
        "size_bytes": len(cleaned), "sha256": record["export"]["sha256"],
        "metadata_cleaned": True,
    }
