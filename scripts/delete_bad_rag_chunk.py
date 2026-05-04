from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

BAD_CONTENT_HASH = "584577d11476cde8fee2624b86658fcd8d7e7a236eaeaedbbb7748123f5af987"

PDF_CHUNKS_FILE = ROOT / "knowledge_pdfs" / "processed" / "knowledge_chunks.jsonl"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def supabase_headers() -> dict[str, str]:
    if not SUPABASE_URL:
        fail("SUPABASE_URL is missing")
    if not SUPABASE_SERVICE_ROLE_KEY:
        fail("SUPABASE_SERVICE_ROLE_KEY is missing")

    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept-Profile": "app",
        "Content-Profile": "app",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def request_json(
    url: str,
    method: str = "GET",
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> Any:
    body = None

    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers or {},
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"HTTP {exc.code} on {method} {url}\n{detail}")
    except Exception as exc:
        fail(f"Request failed on {method} {url}: {exc!r}")


def delete_from_supabase() -> None:
    encoded_hash = urllib.parse.quote(BAD_CONTENT_HASH, safe="")
    url = f"{SUPABASE_URL}/rest/v1/knowledge_chunks?content_hash=eq.{encoded_hash}"

    deleted = request_json(
        url,
        method="DELETE",
        headers=supabase_headers(),
    )

    print("=== SUPABASE DELETE RESULT ===")
    print(f"bad_content_hash={BAD_CONTENT_HASH}")
    print(f"deleted_rows={len(deleted) if isinstance(deleted, list) else 0}")

    if isinstance(deleted, list):
        for row in deleted:
            print(f"deleted_chunk_id={row.get('id')}")
            print(f"deleted_source={row.get('source_filename')}")
            print(f"deleted_page={row.get('page_number')}")
            print(f"deleted_chunk_index={row.get('chunk_index')}")


def remove_from_local_jsonl() -> None:
    print("")
    print("=== LOCAL JSONL CLEANUP ===")
    print(f"file={PDF_CHUNKS_FILE}")

    if not PDF_CHUNKS_FILE.exists():
        fail(f"Missing file: {PDF_CHUNKS_FILE}")

    rows = []
    removed = []

    for line in PDF_CHUNKS_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        item = json.loads(line)

        if item.get("content_hash") == BAD_CONTENT_HASH:
            removed.append(item)
        else:
            rows.append(item)

    backup_file = PDF_CHUNKS_FILE.with_suffix(".jsonl.bak")
    backup_file.write_text(PDF_CHUNKS_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    with PDF_CHUNKS_FILE.open("w", encoding="utf-8", newline="\n") as output:
        for item in rows:
            output.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"backup_created={backup_file}")
    print(f"removed_local_rows={len(removed)}")
    print(f"remaining_local_rows={len(rows)}")

    for item in removed:
        print(f"removed_source={item.get('source_filename')}")
        print(f"removed_page={item.get('page_number')}")
        print(f"removed_chunk_index={item.get('chunk_index')}")
        print(f"removed_content_hash={item.get('content_hash')}")


def main() -> None:
    print("=== DELETE BAD RAG CHUNK ===")
    print(f"supabase_url_present={bool(SUPABASE_URL)}")
    print(f"service_role_key_present={bool(SUPABASE_SERVICE_ROLE_KEY)}")
    print("")

    delete_from_supabase()
    remove_from_local_jsonl()


if __name__ == "__main__":
    main()
