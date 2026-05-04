from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILES = [
    ROOT / "knowledge_pdfs" / "processed" / "knowledge_chunks.jsonl",
    ROOT / "knowledge_texts" / "processed" / "knowledge_text_chunks.jsonl",
]

SEARCH_TERMS = [
    "come across",
    "look after",
    "Back End",
    "Bakend",
    "Digital Renforcy",
    "chatbot de digital renforcy",
    "Résumé de la grammaire disponible",
    "Test de grammaire qui affiche des scores",
]


def main() -> None:
    print("=== LOCAL RAG QUALITY CHECK ===")

    all_chunks = []

    for file_path in FILES:
        print(f"loading={file_path}")
        if not file_path.exists():
            print(f"missing={file_path}")
            continue

        for line in file_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                item["_source_jsonl"] = str(file_path)
                all_chunks.append(item)

    print(f"chunks_loaded={len(all_chunks)}")
    print("")

    for term in SEARCH_TERMS:
        print("=" * 100)
        print(f"TERM: {term}")
        print("-" * 100)

        matches = []
        term_lower = term.lower()

        for item in all_chunks:
            content = item.get("content", "")
            if term_lower in content.lower():
                matches.append(item)

        print(f"matches_count={len(matches)}")

        for item in matches[:10]:
            content = item.get("content", "")
            idx = content.lower().find(term_lower)
            excerpt = content[max(0, idx - 200): idx + len(term) + 350].replace("\n", " ")

            print(f"source_filename={item.get('source_filename')}")
            print(f"page_number={item.get('page_number')}")
            print(f"chunk_index={item.get('chunk_index')}")
            print(f"content_hash={item.get('content_hash')}")
            print(f"excerpt={excerpt}")
            print("")


if __name__ == "__main__":
    main()
