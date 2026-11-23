"""Reproducible topical discovery and a fixed, fresh-cache CLI test sample.

The sample tests retrieval. It does not decide inclusion in the TCC review.
Raw Crossref responses, the frozen sample and every CLI result are retained.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from pypdf import PdfReader


CLI = "/Users/c24580q/.local/bin/papers"
QUERIES = [
    ("flaky-tests", "flaky tests", 300),
    ("test-flakiness", "test flakiness", 300),
    ("nondeterministic-tests", "nondeterministic tests", 150),
    ("ci-test-failures", "continuous integration test failures", 150),
]
SEED_DOIS = [
    "10.1145/2635868.2635920", "10.1145/3510457.3513037",
    "10.1007/s10664-023-10307-w", "10.3390/computers15060372",
]
PLATFORMS = {
    "10.1145": "ACM Digital Library", "10.1109": "IEEE Xplore",
    "10.1007": "SpringerLink", "10.1016": "ScienceDirect",
    "10.1002": "Wiley Online Library", "10.1049": "IET / Wiley",
    "10.3390": "MDPI", "10.7717": "PeerJ", "10.1142": "World Scientific",
    "10.1080": "Taylor & Francis Online", "10.1177": "Sage Journals",
    "10.1155": "Hindawi / Wiley", "10.1515": "De Gruyter Brill",
    "10.3389": "Frontiers", "10.1371": "PLOS",
    "10.4230": "Schloss Dagstuhl / DROPS", "10.5753": "SBC OpenLib",
}
SAMPLE_QUOTAS = {
    "ACM Digital Library": 36, "IEEE Xplore": 38, "SpringerLink": 10,
    "ScienceDirect": 6, "Wiley Online Library": 2, "www.scitepress.org": 1,
    "SBC OpenLib": 2, "joss.theoj.org": 1, "journal.info.unlp.edu.ar": 1,
    "journals.riverpublishers.com": 1, "www.spiedigitallibrary.org": 1, "MDPI": 1,
}
PLATFORM_NAMES = {
    "www.scitepress.org": "SciTePress Digital Library",
    "joss.theoj.org": "Journal of Open Source Software",
    "journal.info.unlp.edu.ar": "Journal of Computer Science and Technology / UNLP",
    "journals.riverpublishers.com": "River Publishers",
    "www.spiedigitallibrary.org": "SPIE Digital Library",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def norm(text):
    return "".join(c.lower() for c in unicodedata.normalize("NFKD", text) if c.isalnum())


def plain(text):
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)


def category(title):
    lower = title.lower()
    # These rules screen technical-test candidates; each candidate is reviewed
    # by the operator before the sample is frozen. No license/date restrictions.
    if re.search(r"flak(?:y|iness|ier)", lower) and re.search(r"test|build|continuous integration", lower):
        return "direct_flaky_testing"
    if re.search(r"non[ -]?determin|intermittent|order.depend", lower) and "test" in lower:
        return "related_nondeterministic_testing"
    if "continuous integration" in lower and re.search(r"test|fail|build", lower):
        return "ci_testing_context"
    return None


def discover(root):
    sources = root / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    pool = {}
    receipts = []
    requests = [(key, query, "https://api.crossref.org/works?" + urlencode({
            "query.title": query, "rows": rows,
            "select": "DOI,title,container-title,publisher,published,type,URL,resource,abstract,author,license,relation",
        }), False) for key, query, rows in QUERIES]
    requests += [("seed-" + str(i + 1), doi,
                  "https://api.crossref.org/works/" + quote(doi, safe=""), True)
                 for i, doi in enumerate(SEED_DOIS)]
    for key, query, url, single in requests:
        source_path = sources / (key + ".crossref.json")
        if source_path.exists():
            data = json.loads(source_path.read_text())
        else:
            request = Request(url, headers={"User-Agent": "TopicalPaperRetrievalTest/0.1"})
            with urlopen(request, timeout=60) as response:
                data = json.load(response)
            save(source_path, data)
            time.sleep(2)
        items = [data["message"]] if single else data["message"]["items"]
        receipts.append({"query": query, "url": url, "retrieved_records": len(items), "raw_path": str(source_path)})
        for item in items:
            title = plain(" ".join(item.get("title", [])))
            group = category(title)
            if not group:
                continue
            doi = item["DOI"].lower()
            if doi not in pool:
                link = item.get("resource", {}).get("primary", {}).get("URL")
                prefix = doi.split("/")[0]
                pool[doi] = {
                    "doi": doi, "title": title, "venue": item.get("container-title", []),
                    "publisher": item.get("publisher"), "publication_type": item.get("type"),
                    "published": item.get("published"),
                    "authors": item.get("author", []), "doi_url": item.get("URL"),
                    "publisher_url": link,
                    "platform": PLATFORMS.get(prefix, urlsplit(link or "").hostname or item.get("publisher", "unclassified")),
                    "platform_classification": "DOI prefix and Crossref publisher/resource metadata; not the PDF delivery host",
                    "abstract": plain(item.get("abstract", "")),
                    "license_metadata": item.get("license", []),
                    "relation_metadata": item.get("relation", {}),
                    "topic_category": group, "found_in": [],
                    "scientific_eligibility": "candidate; full-text CI relevance and review inclusion not assessed",
                }
            pool[doi]["found_in"].append(key)
        print(json.dumps({"query": query, "records": len(items), "topical_pool": len(pool)}), flush=True)
    save(root / "discovery.json", {"created_at_utc": now(), "queries": receipts,
         "filters": {"license": None, "publication_year": None, "publication_type": None},
         "records": list(pool.values())})
    print(json.dumps({"pool": len(pool), "by_platform": dict(Counter(p["platform"] for p in pool.values())),
                      "by_category": dict(Counter(p["topic_category"] for p in pool.values()))}), flush=True)


def select(root):
    target = root / "sample.json"
    if target.exists():
        raise FileExistsError("The sample is frozen; use a new test directory to change it")
    pool = json.loads((root / "discovery.json").read_text())["records"]
    excluded = []
    eligible = []
    for paper in pool:
        reason = None
        if paper["topic_category"] != "direct_flaky_testing":
            reason = "The sample prioritizes direct flaky-software-testing titles over broader CI context"
        elif paper["platform"] not in SAMPLE_QUOTAS:
            reason = "Outside the selected platform strata of this technical sample"
        elif paper["publication_type"] not in {"journal-article", "proceedings-article", "book-chapter"}:
            reason = "Record represents a volume, supplementary file or another non-article object"
        elif re.match(r"^(?:retracted|retraction|notice of retraction|foreword|summary of)", paper["title"], re.I):
            reason = "Retraction or editorial/workshop summary rather than a target technical article"
        elif paper.get("published", {}).get("date-parts", [[0]])[0][0] > 2026:
            reason = "Future-dated publication metadata; not checked for an already available online edition"
        if reason:
            excluded.append({"doi": paper["doi"], "title": paper["title"], "reason": reason})
        else:
            eligible.append(paper)

    def priority(paper):
        seed = paper["doi"] in SEED_DOIS
        companion = "companion" in " ".join(paper["venue"]).lower()
        keyword_score = len(re.findall(r"root caus|mitigat|fix|repair|understand|empirical|survey|developer|continuous integration|factor|reproduc|resource|asynch", paper["title"].lower()))
        return (not seed, companion, -keyword_score, paper["doi"])

    # Resolve exact normalized title duplicates across registrations, including
    # ACM/IEEE co-publication. A journal/conference extension with a different
    # title remains a distinct article, not necessarily a distinct study.
    seen = set()
    groups = defaultdict(list)
    for paper in sorted(eligible, key=priority):
        key = norm(paper["title"])
        if key in seen:
            excluded.append({"doi": paper["doi"], "title": paper["title"],
                             "reason": "Duplicate normalized article title; one registration retained"})
            continue
        seen.add(key)
        groups[paper["platform"]].append(paper)
    for platform, quota in SAMPLE_QUOTAS.items():
        if len(groups[platform]) < quota:
            raise ValueError(f"Not enough reviewed candidates for {platform}: {len(groups[platform])}/{quota}")
        for paper in groups[platform][quota:]:
            excluded.append({"doi": paper["doi"], "title": paper["title"], "reason": "Platform sample quota reached"})
        groups[platform] = groups[platform][:quota]
    papers = []
    for i in range(max(SAMPLE_QUOTAS.values())):
        for platform in SAMPLE_QUOTAS:
            if i < len(groups[platform]):
                paper = dict(groups[platform][i])
                paper.update(number=len(papers) + 1, platform=PLATFORM_NAMES.get(platform, platform),
                             relevance_basis="Title and registered bibliographic metadata explicitly concern software test flakiness; full-text CI scope remains to be assessed")
                papers.append(paper)
    assert len(papers) == len({p["doi"] for p in papers}) == len({norm(p["title"]) for p in papers}) == 100
    sample = {
        "frozen_at_utc": now(), "purpose": "100 distinct topical articles for a technical CLI test, not the TCC's included-study corpus",
        "selection": "Purposive platform-stratified sample, fixed before downloads; title/metadata relevance reviewed by the assistant, not human validated",
        "license_filter": None, "historical_year_range_filter": None,
        "note": "Exclude future-dated records, exact normalized title duplicates, volume/supplement records and retraction/editorial notices from this technical sample. No inference of final scientific eligibility.",
        "platform_counts": dict(Counter(p["platform"] for p in papers)), "papers": papers,
    }
    save(root / "sample-exclusions.json", excluded)
    save(target, sample)
    config = Path(__file__).resolve().parents[1] / ".data" / "private" / "settings.json"
    sources = list((Path(__file__).resolve().parents[1] / "src" / "paper_retrieval").glob("*.py"))
    save(root / "execution-snapshot.json", {"created_at_utc": now(), "cli": CLI,
        "sample_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "operator_config_path": str(config), "operator_config": json.loads(config.read_text()),
        "operator_config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}})
    print(json.dumps({"selected": len(papers), "platform_counts": sample["platform_counts"]}), flush=True)


def verify_pdf(record, result):
    path = Path(result["file_path"])
    content = path.read_bytes()
    reader = PdfReader(path, strict=True)
    first_text = "\n".join(page.extract_text() or "" for page in reader.pages[:3])
    checks = {
        "fresh_download": result["cached"] is False,
        "sha256_matches": hashlib.sha256(content).hexdigest() == result["sha256"],
        "size_matches": len(content) == result["size_bytes"],
        "page_count_matches": len(reader.pages) == result["page_count"] > 0,
        "document_info_removed": reader.metadata is None,
        "root_xmp_removed": reader.xmp_metadata is None,
        "trailer_id_removed": "/ID" not in reader.trailer,
        "doi_in_first_three_pages": norm(record["doi"]) in norm(first_text),
        "title_in_first_three_pages": norm(record["title"]) in norm(first_text),
    }
    # Keep text evidence for identity-review failures, without making the CLI
    # itself responsible for bibliographic matching.
    return checks, first_text[:16000]


def summarize(root):
    sample = json.loads((root / "sample.json").read_text())
    results = []
    by_platform = defaultdict(Counter)
    for paper in sample["papers"]:
        receipt = root / "attempts" / f'{paper["number"]:03}.json'
        if not receipt.exists():
            continue
        record = json.loads(receipt.read_text())
        results.append(record)
        by_platform[record["platform"]][record["status"]] += 1
    summary = {
        "summarized_at_utc": now(), "selected_articles": len(sample["papers"]),
        "distinct_selected_dois": len({p["doi"] for p in sample["papers"]}),
        "tested_articles": len(results), "not_tested": len(sample["papers"]) - len(results),
        "downloads": sum(bool(r.get("result", {}).get("ok")) for r in results),
        "fresh_downloads": sum(r.get("result", {}).get("cached") is False for r in results),
        "statuses": dict(Counter(r["status"] for r in results)),
        "errors": dict(Counter(r.get("result", {}).get("error", {}).get("code", r.get("test_error", "unknown"))
                               for r in results if not r.get("result", {}).get("ok"))),
        "by_platform": {key: dict(value) for key, value in by_platform.items()},
        "delivery_hosts": dict(Counter(urlsplit(r["acquisition"]["download_url"]).hostname
                                       for r in results if "acquisition" in r)),
        "verification_challenge_attempts": sum(bool(r.get("verification_used")) for r in results),
        "total_downloaded_bytes": sum(r.get("result", {}).get("size_bytes", 0) for r in results),
        "test_started_at_utc": min((r["started_at_utc"] for r in results), default=None),
        "test_finished_at_utc": max((r["finished_at_utc"] for r in results), default=None),
        "note": "Fixed technical test sample; no formal TCC inclusion decisions or systematic-review findings.",
    }
    save(root / "results.json", results)
    save(root / "summary.json", summary)
    return summary


def run(root):
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    sample = json.loads((root / "sample.json").read_text())
    papers = sample["papers"]
    if len(papers) != 100 or len({p["doi"] for p in papers}) != 100:
        raise ValueError("The frozen sample must contain exactly 100 distinct DOIs")
    (root / "attempts").mkdir(exist_ok=True)
    for paper in papers:
        target = root / "attempts" / f'{paper["number"]:03}.json'
        if target.exists():
            continue
        directory = root / "downloads" / f'{paper["number"]:03}'
        if directory.exists():
            raise RuntimeError(f"Unrecorded collection exists: {directory}")
        command = [CLI, "--data-dir", str(directory), "retrieve", paper["doi"]]
        started = time.monotonic()
        record = {**paper, "command": command, "started_at_utc": now(), "collection_initially_empty": True}
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=120)
            record.update(exit_code=process.returncode, result=json.loads(process.stdout))
            if record["result"].get("ok"):
                checks, evidence = verify_pdf(paper, record["result"])
                record["checks"] = checks
                if not all(checks.values()):
                    record["identity_text_evidence"] = evidence
                record["status"] = "validated" if all(checks.values()) else "downloaded_needs_review"
                acquisition = directory / "private" / (record["result"]["paper_id"] + ".json")
                record["acquisition"] = json.loads(acquisition.read_text())["acquisition"]
            else:
                record["status"] = "failed"
        except Exception as error:
            record.update(status="test_error", test_error=type(error).__name__, detail=str(error))
        log = directory / "private" / "cli-errors.log"
        if log.exists():
            value = log.read_text()
            record["verification_used"] = "bounded_pow_v1" in value
            if record["status"] != "validated":
                record["private_diagnostic"] = value[-3000:]
        record.update(elapsed_seconds=round(time.monotonic() - started, 2), finished_at_utc=now())
        save(target, record)
        summary = summarize(root)
        print(json.dumps({"number": paper["number"], "doi": paper["doi"], "platform": paper["platform"],
                          "status": record["status"], "error": record.get("result", {}).get("error"),
                          "progress": summary["tested_articles"], "downloads": summary["downloads"]}), flush=True)
        if record.get("result", {}).get("error", {}).get("code") in {
            "network_permission_denied", "rate_limited", "verification_required",
        }:
            print("Batch paused; receipts preserved. Inspect the operational condition before resuming.", flush=True)
            break
        time.sleep(2)


def finalize(root):
    """Verify the completed run and publish a readable index of its PDFs."""
    summary = summarize(root)
    records = json.loads((root / "results.json").read_text())
    sample = json.loads((root / "sample.json").read_text())
    snapshot = json.loads((root / "execution-snapshot.json").read_text())
    independent = json.loads((root / "independent-validation.json").read_text())
    independent_by_number = {r["number"]: r for r in independent["records"]}
    audit = {
        "checked_at_utc": now(),
        "exactly_100_unique_articles_tested": len(records) == len({r["doi"] for r in records}) == 100,
        "receipt_dois_match_frozen_sample": [r["doi"] for r in records] == [p["doi"] for p in sample["papers"]],
        "frozen_sample_unchanged": hashlib.sha256((root / "sample.json").read_bytes()).hexdigest() == snapshot["sample_sha256"],
        "operator_config_unchanged": hashlib.sha256(Path(snapshot["operator_config_path"]).read_bytes()).hexdigest() == snapshot["operator_config_sha256"],
        "retrieval_implementation_unchanged": all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest
                                                for p, digest in snapshot["source_sha256"].items()),
    }
    hosts = [urlsplit(url).hostname for url in snapshot["operator_config"]["provider_urls"]]
    audit["provider_hosts_absent_from_all_public_cli_results"] = all(
        not any(host in json.dumps(r.get("result", {})) for host in hosts) for r in records)
    index = []
    folder = root / "pdfs"
    folder.mkdir(exist_ok=True)
    for record in records:
        result = record.get("result", {})
        entry = {key: record[key] for key in ("number", "doi", "title", "platform", "venue", "published", "status", "elapsed_seconds")}
        entry.update(doi_url="https://doi.org/" + record["doi"], downloaded=bool(result.get("ok")))
        if result.get("ok"):
            content = Path(result["file_path"]).read_bytes()
            if result["cached"] or hashlib.sha256(content).hexdigest() != result["sha256"]:
                raise ValueError("Download freshness/integrity mismatch")
            reader = PdfReader(result["file_path"], strict=True)
            if len(reader.pages) != result["page_count"] or reader.metadata is not None or reader.xmp_metadata is not None:
                raise ValueError("PDF structure or metadata mismatch")
            if any("/Metadata" in page for page in reader.pages) or "/ID" in reader.trailer:
                raise ValueError("Page metadata or document identifier still present")
            check = independent_by_number[record["number"]]
            reviewed = check.get("visual_review", {})
            if not ((check["title_in_first_page_poppler"] or reviewed.get("title_confirmed"))
                    and (check["doi_in_first_page_poppler"] or reviewed.get("doi_confirmed"))
                    and check["sha256"] == result["sha256"]):
                raise ValueError("Independent identity check unresolved")
            slug = unicodedata.normalize("NFKD", record["title"]).encode("ascii", "ignore").decode().lower()
            slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")[:110]
            link = folder / f'{record["number"]:03}-{slug}.pdf'
            source = Path(result["file_path"])
            if link.is_symlink() or link.exists():
                if link.resolve() != source:
                    raise FileExistsError(link)
            else:
                link.symlink_to(os.path.relpath(source, link.parent))
            entry.update(file_path=str(link), original_export_path=str(source), sha256=result["sha256"],
                         page_count=result["page_count"], metadata_cleaned=True)
        else:
            entry["error"] = result.get("error", {"code": record.get("test_error", "unknown")})
        index.append(entry)
    audit["successful_pdfs_independently_checked"] = len(independent_by_number) == summary["downloads"]
    audit["friendly_pdf_links_verified"] = len(list(folder.glob("*.pdf"))) == summary["downloads"] and all(p.is_file() for p in folder.glob("*.pdf"))
    save(root / "audit.json", audit)
    if not all(value for key, value in audit.items() if key != "checked_at_utc"):
        raise ValueError("Final audit failed")
    summary["validated_total"] = sum(r["status"] in {"validated", "validated_after_review"} for r in records)
    save(root / "summary.json", summary)
    save(root / "report.json", {"summary": summary, "audit": audit, "articles": index})
    lines = ["Teste de recuperação de 100 artigos sobre testes intermitentes", "",
             f'100 artigos distintos testados em {len(sample["platform_counts"])} plataformas; {summary["downloads"]} PDFs obtidos e validados; {100-summary["downloads"]} falhas.',
             "Amostra fechada antes dos downloads, selecionada por títulos/metadados. Sem filtro de licença ou recorte histórico de anos.",
             "Todos os downloads usaram coleções novas. Os PDFs estão em pdfs/ com nomes legíveis, por links para as cópias exportadas e verificadas.",
             "As falhas foram preservadas. Nenhum artigo foi substituído para aumentar a taxa de sucesso.",
             "Esta é uma amostra de teste da ferramenta. A aderência integral a CI, qualidade metodológica e inclusão na RSL permanecem pendentes.",
             "", "Plataformas — PDFs obtidos / artigos testados:"]
    for platform, count in sample["platform_counts"].items():
        successes = sum(r["downloaded"] for r in index if r["platform"] == platform)
        lines.append(f"- {platform}: {successes}/{count}")
    lines += ["", "Falhas:"] + [f"- {code}: {count}" for code, count in summary["errors"].items()]
    lines += ["", "Conferência: título, DOI, páginas, SHA-256, tamanho e remoção de metadados; extração independente com Poppler e conferência visual das exceções pelo assistente.",
              "Configuração e implementação de recuperação mantidas durante os 100 testes. Proveniência operacional preservada nos registros privados.", "", "Artigos e resultados:"]
    for r in index:
        lines += ["", f'[{r["number"]:03}] {r["title"]}', f'Plataforma: {r["platform"]}', f'DOI: {r["doi"]}',
                  f'Resultado: {r["status"]}' + (f' — {r["error"]["code"]}' if "error" in r else ""),
                  f'PDF: {r["file_path"]}' if r["downloaded"] else "PDF não entregue."]
    (root / "report.txt").write_text("\n".join(lines) + "\n")
    print(json.dumps({"summary": summary, "audit": audit}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("discover", "select", "run", "summarize", "finalize"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.phase == "discover":
        discover(root)
    elif args.phase == "select":
        select(root)
    elif args.phase == "run":
        run(root)
    elif args.phase == "finalize":
        finalize(root)
    else:
        print(json.dumps(summarize(root), ensure_ascii=False))
