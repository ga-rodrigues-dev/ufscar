import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from paper_retrieval.core import Document, PaperStore, validate_pdf
from paper_retrieval.pdf_export import clean_metadata, export_clean_pdf


def fixture():
    writer = PdfWriter()
    page = writer.add_blank_page(width=100, height=100)
    writer.add_metadata({"/Author": "PRIVATE_AUTHOR_MARKER", "/Producer": "PRIVATE_PRODUCER_MARKER"})
    for target, marker in ((writer.root_object, b"PRIVATE_ROOT_XMP"), (page, b"PRIVATE_PAGE_XMP")):
        metadata = DecodedStreamObject()
        metadata.set_data(b'<x:xmpmeta xmlns:x="adobe:ns:meta/">' + marker + b'</x:xmpmeta>')
        metadata[NameObject("/Type")] = NameObject("/Metadata")
        metadata[NameObject("/Subtype")] = NameObject("/XML")
        target[NameObject("/Metadata")] = writer._add_object(metadata)
    content = DecodedStreamObject()
    content.set_data(b"0 0 10 10 re S")
    page[NameObject("/Contents")] = writer._add_object(content)
    writer.generate_file_identifiers()
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class ExportTests(unittest.TestCase):
    def test_recoverable_duplicate_dictionary_key_is_rewritten_cleanly(self):
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /MediaBox [0 0 100 100] /Resources <<>> >>",
        ]
        original = bytearray(b"%PDF-1.4\n")
        offsets = []
        for index, obj in enumerate(objects, 1):
            offsets.append(len(original))
            original.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(original)
        original.extend(b"xref\n0 4\n0000000000 65535 f \n")
        for offset in offsets:
            original.extend(f"{offset:010d} 00000 n \n".encode())
        original.extend(f"trailer\n<< /Root 1 0 R /Size 4 >>\nstartxref\n{xref}\n%%EOF\n".encode())
        with self.assertRaises(Exception):
            strict = PdfReader(io.BytesIO(original), strict=True)
            len(strict.pages)
        self.assertEqual(validate_pdf(bytes(original)), 1)
        cleaned = clean_metadata(bytes(original))
        checked = PdfReader(io.BytesIO(cleaned), strict=True)
        self.assertEqual(len(checked.pages), 1)
        self.assertEqual(list(checked.pages[0].mediabox), [0, 0, 100, 100])
        self.assertIsNone(checked.metadata)

    def test_metadata_removed_and_page_content_preserved(self):
        original = fixture()
        cleaned = clean_metadata(original)
        reader = PdfReader(io.BytesIO(cleaned))
        self.assertIsNone(reader.metadata)
        self.assertIsNone(reader.xmp_metadata)
        self.assertNotIn("/Metadata", reader.pages[0])
        self.assertNotIn("/ID", reader.trailer)
        for marker in (b"PRIVATE_AUTHOR_MARKER", b"PRIVATE_PRODUCER_MARKER", b"PRIVATE_ROOT_XMP", b"PRIVATE_PAGE_XMP"):
            self.assertNotIn(marker, cleaned)
            self.assertNotIn(marker.replace(b"_", b"\\137"), cleaned)
        self.assertEqual(reader.pages[0].get_contents().get_data(), b"0 0 10 10 re S")
        self.assertEqual(PdfReader(io.BytesIO(original)).metadata.author, "PRIVATE_AUTHOR_MARKER")

    def test_original_receipt_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PaperStore(Path(directory))
            original = fixture()
            paper = store.save("10.1234/export", Document(original, "https://private.example", "https://private.example/paper.pdf", 1))
            output = Path(directory) / "clean.pdf"
            result = export_clean_pdf(store, paper, output)
            self.assertTrue(result["metadata_cleaned"])
            self.assertEqual(result["sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(result["size_bytes"], output.stat().st_size)
            self.assertEqual(Path(paper.file_path).read_bytes(), original)
            receipts = [json.loads(path.read_text()) for path in store.private.glob("export-*.json")]
            self.assertEqual(receipts[0]["status"], "complete")
            self.assertEqual(receipts[0]["original"]["sha256"], paper.sha256)
            self.assertEqual(receipts[0]["export"]["sha256"], result["sha256"])
            with self.assertRaises(FileExistsError):
                export_clean_pdf(store, paper, output)
            with self.assertRaises(FileExistsError):
                export_clean_pdf(store, paper, Path(paper.file_path))


if __name__ == "__main__":
    unittest.main()
