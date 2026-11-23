#!/usr/bin/env python3
"""Submit the local lecture recordings to Soniox and retain provider transcripts.

Resumes jobs from ignored staging state and confirms deletion of remote resources.
Run from the repository root with SONIOX_API_KEY in the environment or .env.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "metodologia-cientifica"
STAGE = ROOT / ".soniox-staging"
BASE = "https://api.soniox.com/v1"


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def request(key: str, method: str, endpoint: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(BASE + endpoint, data=data, method=method,
                  headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=120) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Soniox {method} {endpoint}: HTTP {exc.code}") from None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Soniox {method} {endpoint}: {type(exc).__name__}") from None


def upload(key: str, path: Path) -> str:
    boundary = "----lecture" + uuid.uuid4().hex
    mime = mimetypes.guess_type(path.name)[0] or "audio/mp4"
    prefix = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
              f"filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n").encode()
    suffix = f"\r\n--{boundary}--\r\n".encode()
    # urllib requires a complete request body. Process one lecture at a time.
    req = Request(BASE + "/files", data=prefix + path.read_bytes() + suffix, method="POST",
                  headers={"Authorization": "Bearer " + key,
                           "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urlopen(req, timeout=1200) as response:
            return json.load(response)["id"]
    except HTTPError as exc:
        raise RuntimeError(f"Soniox upload: HTTP {exc.code}") from None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Soniox upload: {type(exc).__name__}") from None


def delete(key: str, endpoint: str) -> bool:
    req = Request(BASE + endpoint, method="DELETE", headers={"Authorization": "Bearer " + key})
    try:
        with urlopen(req, timeout=120):
            return True
    except HTTPError as exc:
        if exc.code == 404:
            return True
        print(f"Cleanup pending for {endpoint}: HTTP {exc.code}", file=sys.stderr)
        return False
    except (URLError, TimeoutError) as exc:
        print(f"Cleanup pending for {endpoint}: {type(exc).__name__}", file=sys.stderr)
        return False


def transcript_markdown(recording: Path, source: Path, result: dict, context: dict,
                        segment_start: int, model: str = "stt-async-v5") -> str:
    lines = [f"# {recording.stem} — Soniox transcript", "",
             f"- Recording: [{source.name}](../../gravacoes/{source.name.replace(' ', '%20')})",
             f"- Provider: Soniox `{model}`",
             "- Language hints: Portuguese and English",
             "- Speaker labels: automatic, unreviewed", "",
             "## Context sent to Soniox", "", context["general"][1]["value"], "",
             "## Transcript", ""]
    if segment_start:
        lines.insert(3, f"- Segment begins at {segment_start // 3600:02}:{(segment_start % 3600) // 60:02}:{segment_start % 60:02} in the original recording")
    tokens = result.get("tokens") or result.get("words") or []
    if not isinstance(tokens, list):
        raise RuntimeError("Soniox result has no token list")
    speaker = None
    parts: list[str] = []
    chunk_start_ms = 0

    def flush() -> None:
        if not parts:
            return
        seconds = (chunk_start_ms // 1000) + segment_start
        stamp = f"{seconds // 3600:02}:{(seconds % 3600) // 60:02}:{seconds % 60:02}"
        lines.extend([f"**[{stamp}] Speaker {speaker}:** {''.join(parts).strip()}", ""])

    for token in tokens:
        if not isinstance(token, dict):
            continue
        current = token.get("speaker") or token.get("speaker_id") or "unknown"
        word = token.get("text") or token.get("word") or ""
        if speaker is not None and (current != speaker or
                                    (sum(map(len, parts)) >= 1000 and
                                     str(parts[-1]).rstrip().endswith((".", "?", "!")))):
            flush()
            parts = []
        if not parts:
            chunk_start_ms = int(token.get("start_ms") or 0)
        speaker = current
        parts.append(str(word))
    if parts:
        flush()
    elif result.get("text"):
        lines.extend([str(result["text"]), ""])
    else:
        raise RuntimeError("Soniox result contains no transcript text")
    return "\n".join(lines)


def process(recording: Path, key: str, config: dict, *, source: Path | None = None,
            segment_start: int = 0, retry_failed: bool = False) -> None:
    source = source or recording
    with recording.open("rb") as audio_file:
        pointer_header = audio_file.read(40)
    if recording.stat().st_size < 1000 or pointer_header.startswith(b"version https://git-lfs"):
        raise RuntimeError(f"{recording.name}: Git LFS audio has not been downloaded")
    date = recording.name[:10]
    lesson = config["lectures"][date]
    model = lesson.get("model", "stt-async-v5")
    context = {"general": [
        {"key": "course", "value": config["course"]},
        {"key": "topic", "value": lesson["topic"]},
        {"key": "setting", "value": "University lecture in Brazilian Portuguese"},
    ], "terms": lesson["terms"]}
    raw_dir = COURSE / "transcricoes" / "raw"
    out = raw_dir / (recording.stem + ".soniox-original.pt.md")
    raw = raw_dir / (recording.stem + ".soniox-result.json")
    state_path = STAGE / (date + "-" + hashlib.sha256(recording.name.encode()).hexdigest()[:12] + ".json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    hasher = hashlib.sha256()
    with recording.open("rb") as audio_file:
        for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    if state and state.get("sha256") != digest:
        raise RuntimeError(f"{recording.name}: recording changed since submission")
    if state.get("job_id") and state.get("model", "stt-async-v5") != model:
        raise RuntimeError(f"{recording.name}: model changed since submission")
    if state.get("job_id_deleted") and not raw.exists():
        if not retry_failed:
            reason = (state.get("terminal_error") or {}).get("error_type") or "no transcript returned"
            raise RuntimeError(f"{recording.name}: previous Soniox job failed ({reason}); use --retry-failed after resolving the cause")
        state_path.rename(state_path.with_name(state_path.stem + f".failed-{int(time.time())}.json"))
        state = {}
    state.setdefault("sha256", digest)
    state.setdefault("model", model)
    state.setdefault("context", context)
    if state["context"] != context and state.get("job_id"):
        raise RuntimeError(f"{recording.name}: context changed since submission")
    save(state_path, state)
    print(f"Processing {recording.name}", flush=True)
    terminal = raw.exists()
    try:
        if not raw.exists():
            if not state.get("file_id"):
                state["file_id"] = upload(key, recording)
                save(state_path, state)
            if not state.get("job_id"):
                job = request(key, "POST", "/transcriptions", {
                    "model": model, "file_id": state["file_id"],
                    "client_reference_id": recording.stem[:256],
                    "language_hints": config["language_hints"], "context": context,
                    "enable_speaker_diarization": True,
                    "enable_language_identification": True,
                })
                state["job_id"] = job["id"]
                save(state_path, state)
            deadline = time.monotonic() + 7200
            while True:
                job = request(key, "GET", "/transcriptions/" + state["job_id"])
                status = job.get("status")
                if status in ("completed", "error", "failed"):
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError("Soniox job timed out; retry will resume it")
                time.sleep(15)
            if status != "completed":
                terminal = True
                state["terminal_error"] = {
                    "status": status,
                    "error_type": job.get("error_type"),
                    "error_message": job.get("error_message"),
                }
                save(state_path, state)
                raise RuntimeError(f"Soniox job ended with status {status}: {job.get('error_type') or 'unknown error'}")
            result = request(key, "GET", "/transcriptions/" + state["job_id"] + "/transcript")
            save(raw, result)
            terminal = True
        else:
            result = json.loads(raw.read_text())
        if not out.exists():
            out.write_text(transcript_markdown(recording, source, result, context, segment_start, model))
    finally:
        if terminal or not state.get("job_id"):
            for field, endpoint in (("job_id", "/transcriptions/"), ("file_id", "/files/")):
                if state.get(field) and not state.get(field + "_deleted"):
                    state[field + "_deleted"] = delete(key, endpoint + state[field])
                    save(state_path, state)
    if not all(state.get(field + "_deleted", True) for field in ("job_id", "file_id")):
        raise RuntimeError(f"{recording.name}: remote cleanup pending; rerun to retry")
    print(f"Saved {out.relative_to(ROOT)}", flush=True)


def main() -> int:
    retry_failed = "--retry-failed" in sys.argv[1:]
    env = ROOT / ".env"
    key = os.environ.get("SONIOX_API_KEY")
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("SONIOX_API_KEY="):
                key = line.partition("=")[2].strip().strip('"\'')
    if not key:
        raise RuntimeError("SONIOX_API_KEY is missing")
    config = json.loads((COURSE / "transcricoes" / "raw" / "transcription-context.json").read_text())
    recordings = sorted((COURSE / "gravacoes").glob("*.m4a"))
    filters = [item for item in sys.argv[1:] if item != "--retry-failed"]
    if filters:
        recordings = [item for item in recordings if any(filter_text in item.name for filter_text in filters)]
    if not recordings:
        raise RuntimeError("No lecture recordings found")
    failures = []
    for recording in recordings:
        try:
            if recording.name.startswith("2026-09-19 0756"):
                for segment, start in ((1, 0), (2, 9600)):
                    clip = STAGE / "audio" / f"{recording.stem} - Segmento {segment}.m4a"
                    if not clip.exists():
                        clip.parent.mkdir(parents=True, exist_ok=True)
                        temporary = clip.with_name(clip.stem + ".tmp.m4a")
                        command = ["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", str(start),
                                   "-i", str(recording)]
                        if segment == 1:
                            command.extend(["-t", "9600"])
                        command.extend(["-c", "copy", "-y", str(temporary)])
                        subprocess.run(command, check=True)
                        temporary.replace(clip)
                    process(clip, key, config, source=recording, segment_start=start,
                            retry_failed=retry_failed)
            else:
                process(recording, key, config, retry_failed=retry_failed)
        except Exception as exc:
            print(f"ERROR {recording.name}: {exc}", file=sys.stderr)
            failures.append(recording.name)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
