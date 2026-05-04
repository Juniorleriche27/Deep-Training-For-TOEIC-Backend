from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.knowledge import retrieve_knowledge_chunks, retrieve_knowledge_context


async def main() -> None:
    query = "Explique-moi les phrasal verbs come across et look after."

    chunks = await retrieve_knowledge_chunks(query)
    print(f"chunks_count={len(chunks)}")

    for index, chunk in enumerate(chunks[:3], start=1):
        print("=" * 80)
        print(f"[{index}] source={chunk.get('source_filename')}")
        print(f"keyword_rank={chunk.get('keyword_rank')}")
        print(f"final_score={chunk.get('final_score')}")
        print((chunk.get("content") or "")[:500].replace("\n", " "))

    context = await retrieve_knowledge_context(query)
    print("=" * 80)
    print(f"context_chars={len(context)}")
    print(context[:1000].replace("\n", " "))


if __name__ == "__main__":
    asyncio.run(main())
