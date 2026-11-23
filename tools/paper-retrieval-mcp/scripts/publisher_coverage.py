"""Discover verifiable DOI samples and test the installed papers CLI.

This is an exploratory test of article availability, not a publisher connector
test or a systematic literature search. Discovery and execution are separate.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from collections import Counter
import re
import subprocess
import time
import unicodedata
from urllib.parse import urlencode
import urllib.request

from pypdf import PdfReader
from bs4 import BeautifulSoup


PLATFORMS = [
    ("elsevier", "Elsevier / ScienceDirect", "2405-8440", "Heliyon"),
    ("springer", "SpringerLink", "1588-2861", "Scientometrics"),
    ("nature", "Nature.com", "2045-2322", "Scientific Reports"),
    ("wiley", "Wiley Online Library", "2045-7758", "Ecology and Evolution"),
    ("taylor-francis", "Taylor & Francis Online", "2331-1916", "Cogent Engineering"),
    ("sage", "Sage Journals", "2158-2440", "SAGE Open"),
    ("oxford", "Oxford Academic", "1362-4962", "Nucleic Acids Research"),
    ("cambridge", "Cambridge Core", "2632-6736", "Data-Centric Engineering"),
    ("acs", "ACS Publications", "2470-1343", "ACS Omega"),
    ("aps", "APS Journals", "2160-3308", "Physical Review X"),
    ("aip", "AIP Publishing", "2158-3226", "AIP Advances"),
    ("iop", "IOPscience", "1367-2630", "New Journal of Physics"),
    ("ieee", "IEEE Xplore", "2169-3536", "IEEE Access"),
    ("acm", "ACM Digital Library", "2573-0142", "Proceedings of the ACM on Human-Computer Interaction"),
    ("plos", "PLOS", "1932-6203", "PLOS ONE"),
    ("elife", "eLife", "2050-084X", "eLife"),
    ("peerj", "PeerJ", "2167-8359", "PeerJ"),
    ("frontiers", "Frontiers", "1662-453X", "Frontiers in Neuroscience"),
    ("mdpi", "MDPI", "1424-8220", "Sensors"),
    ("royal-society", "Royal Society Publishing", "2054-5703", "Royal Society Open Science"),
    ("pnas", "PNAS", "1091-6490", "Proceedings of the National Academy of Sciences"),
    ("bmj", "BMJ", "2044-6055", "BMJ Open"),
    ("aaas", "AAAS / Science.org", "2375-2548", "Science Advances"),
    ("scielo", "SciELO", "1678-4375", "Brazilian Journal of Biology"),
    ("copernicus", "Copernicus Publications", "1991-9603", "Geoscientific Model Development"),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(value: str) -> str:
    return "".join(char.lower() for char in unicodedata.normalize("NFKD", value) if char.isalnum())


def save(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def summarize(root: Path) -> dict:
    """Rebuild aggregates from receipts, including retries and identity reviews."""
    manifest = json.loads((root / "manifest.json").read_text())
    reports = []
    for platform in manifest["platforms"]:
        path = root / (platform["id"] + ".result.json")
        reports.append(json.loads(path.read_text()) if path.exists() else {
            "id": platform["id"], "platform": platform["platform"],
            "attempts": [], "status": "not_tested",
        })
    attempts = [attempt for report in reports for attempt in report["attempts"]]
    successes = [attempt for attempt in attempts if attempt.get("result", {}).get("ok")]
    errors = Counter(attempt.get("result", {}).get("error", {}).get("code", "test_error")
                     for attempt in attempts if not attempt.get("result", {}).get("ok"))
    summary = {
        "summarized_at_utc": now(), "platforms_selected": len(reports),
        "validated": sum(r["status"] in {"validated", "validated_after_review"} for r in reports),
        "validated_automatically": sum(r["status"] == "validated" for r in reports),
        "validated_after_review": sum(r["status"] == "validated_after_review" for r in reports),
        "downloaded_needs_review": sum(r["status"] == "downloaded_needs_review" for r in reports),
        "failed": sum(r["status"] in {"failed", "test_error"} for r in reports),
        "not_tested": sum(r["status"] == "not_tested" for r in reports),
        "article_attempts": len(attempts),
        "distinct_dois": len({a["doi"].lower() for a in attempts}),
        "successful_downloads": len(successes),
        "fresh_downloads": sum(a["result"]["cached"] is False for a in successes),
        "failed_attempts": len(attempts) - len(successes),
        "first_attempt_downloads": sum(bool(r["attempts"]) and
                                       bool(r["attempts"][0].get("result", {}).get("ok"))
                                       for r in reports),
        "error_counts": dict(errors),
        "verification_challenge_attempts": sum(bool(a.get("verification_used")) for a in attempts),
        "download_hosts": dict(Counter(a["acquisition"]["download_url"].split("/")[2]
                                       for a in successes if "acquisition" in a)),
        "test_started_at_utc": min((a["started_at_utc"] for a in attempts), default=None),
        "test_finished_at_utc": max((r.get("finished_at_utc", "") for r in reports), default=None),
        "scope": "Availability of sampled papers via configured DOI retrieval; not direct publisher connectors or exhaustive journal coverage.",
    }
    save(root / "results.json", reports)
    save(root / "summary.json", summary)
    return summary


def discover(root: Path) -> None:
    (root / "sources").mkdir(parents=True, exist_ok=True)
    def lookup(platform):
        key, name, issn, journal = platform
        query = urlencode({
            "filter": "from-pub-date:2018-01-01,until-pub-date:2020-12-31,type:journal-article,has-license:true",
            "rows": 30, "sort": "published", "order": "asc",
        })
        url = f"https://api.crossref.org/journals/{issn}/works?{query}"
        record = {"id": key, "platform": name, "journal_expected": journal, "issn": issn,
                  "discovery_url": url, "discovered_at_utc": now(), "candidates": []}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "PaperRetrievalCoverageTest/0.1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
            save(root / "sources" / (key + ".crossref.json"), data)
            items = data["message"]["items"]
            record["records_examined"] = len(items)
            for item in items:
                licenses = [entry["URL"] for entry in item.get("license", [])
                            if "creativecommons.org/" in entry.get("URL", "").lower()
                            and "-nd/" not in entry.get("URL", "").lower()]
                title = BeautifulSoup(" ".join(item.get("title", [])), "html.parser").get_text(" ", strip=True)
                if not licenses or not title or re.match(r"^(?:(?:author|publisher)\s+)?(?:correction|erratum|corrigendum|retraction)\b", title, re.I):
                    continue
                containers = item.get("container-title", [])
                if not any(normalize(journal) == normalize(container) for container in containers):
                    continue
                record["candidates"].append({
                    "doi": item["DOI"], "title": title, "journal": containers,
                    "publisher": item.get("publisher"), "published": item.get("published"),
                    "license_urls": list(dict.fromkeys(licenses)), "doi_url": item.get("URL"),
                    "publisher_url": item.get("resource", {}).get("primary", {}).get("URL"),
                })
                if len(record["candidates"]) == 3:
                    break
            record["discovery_status"] = "ready" if record["candidates"] else "no_eligible_metadata"
        except Exception as error:
            record.update(discovery_status="failed", discovery_error=type(error).__name__, detail=str(error))
        save(root / "sources" / (key + ".selection.json"), record)
        print(json.dumps({"platform": name, "discovery": record["discovery_status"],
                          "candidates": [{"doi": c["doi"], "title": c["title"]} for c in record["candidates"]]}, ensure_ascii=False), flush=True)
        return record
    with ThreadPoolExecutor(max_workers=3) as executor:
        records = list(executor.map(lookup, PLATFORMS))
    save(root / "manifest.json", {"created_at_utc": now(), "selection": {
        "scope": "25 selected publication platforms; one journal per platform",
        "years": "2018–2020", "sort": "published ascending",
        "metadata_rows_per_platform": 30, "eligible_license": "Creative Commons without ND",
        "note": "Exploratory sample; neither exhaustive nor statistically random. Metadata availability is not download success.",
    }, "platforms": records})


def run(root: Path, attempts_per_platform: int, resume: bool = False) -> None:
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    manifest = json.loads((root / "manifest.json").read_text())
    reports = []
    for platform in manifest["platforms"]:
        existing = root / (platform["id"] + ".result.json")
        if resume and existing.exists():
            previous = json.loads(existing.read_text())
            if previous["status"] != "not_tested":
                reports.append(previous)
                continue
        report = {key: platform[key] for key in ("id", "platform", "journal_expected", "discovery_url")}
        report.update(started_at_utc=now(), attempts=[], status="not_tested")
        for index, candidate in enumerate(platform["candidates"][:attempts_per_platform]):
            directory = (root / "downloads" / platform["id"] / str(index + 1)).resolve()
            if directory.exists():
                raise RuntimeError("A test collection already exists; use a new run directory")
            started = time.monotonic()
            command = ["/Users/c24580q/.local/bin/papers", "--data-dir", str(directory), "retrieve", candidate["doi"]]
            attempt = {**candidate, "command": command, "started_at_utc": now(), "collection_initially_empty": True}
            try:
                process = subprocess.run(command, capture_output=True, text=True, timeout=120)
                result = json.loads(process.stdout)
                attempt.update(exit_code=process.returncode, result=result)
                if result.get("ok"):
                    path = Path(result["file_path"])
                    reader = PdfReader(path, strict=True)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages[:3])
                    attempt["checks"] = {
                        "fresh_download": result["cached"] is False,
                        "size_matches": len(path.read_bytes()) == result["size_bytes"],
                        "sha256_matches": hashlib.sha256(path.read_bytes()).hexdigest() == result["sha256"],
                        "page_count_matches": len(reader.pages) == result["page_count"] > 0,
                        "doi_in_first_three_pages": normalize(candidate["doi"]) in normalize(text),
                        "title_in_first_three_pages": normalize(candidate["title"]) in normalize(text),
                        "document_info_removed": reader.metadata is None,
                        "xmp_removed": reader.xmp_metadata is None,
                    }
                    original = json.loads((directory / "private" / (result["paper_id"] + ".json")).read_text())
                    attempt["acquisition"] = original["acquisition"]
                    attempt["status"] = "validated" if all(attempt["checks"].values()) else "downloaded_needs_review"
                else:
                    attempt["status"] = "failed"
            except Exception as error:
                attempt.update(status="test_error", test_error=type(error).__name__, detail=str(error))
            attempt["elapsed_seconds"] = round(time.monotonic() - started, 2)
            log = directory / "private" / "cli-errors.log"
            if log.exists():
                attempt["verification_used"] = "bounded_pow_v1" in log.read_text()
                if attempt["status"] != "validated":
                    attempt["private_diagnostic"] = log.read_text()[-2400:]
            report["attempts"].append(attempt)
            report["status"] = attempt["status"]
            save(root / (platform["id"] + ".result.json"), report)
            print(json.dumps({"platform": platform["platform"], "doi": candidate["doi"],
                              "status": attempt["status"], "seconds": attempt["elapsed_seconds"],
                              "error": attempt.get("result", {}).get("error"), "checks": attempt.get("checks")}, ensure_ascii=False), flush=True)
            if attempt["status"] != "failed" or attempt.get("result", {}).get("error", {}).get("code") not in {"not_found", "no_pdf_link", "invalid_document"}:
                break
            time.sleep(2)
        report["finished_at_utc"] = now()
        reports.append(report)
        save(root / (platform["id"] + ".result.json"), report)
        save(root / "results.json", reports)
        if report["attempts"] and report["attempts"][-1].get("result", {}).get("error", {}).get("code") in {"rate_limited", "network_permission_denied"}:
            print("Batch paused: network permission or service rate limit. Results saved.", flush=True)
            return
        time.sleep(2)
    summary = summarize(root)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("discover", "run", "summarize"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--attempts-per-platform", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    if args.phase == "discover":
        discover(args.directory)
    elif args.phase == "summarize":
        print(json.dumps(summarize(args.directory), ensure_ascii=False))
    else:
        run(args.directory, args.attempts_per_platform, args.resume)
