"""Query a reproducible metadata snapshot from the official ACL Anthology."""
import json
import re
from pathlib import Path
from app.schemas.paper import PaperSearchResult
CORPUS_PATH = Path(__file__).resolve().parents[3] / "data" / "nlp_corpus.json"
STOP = {"the", "and", "of", "for", "in", "to", "how", "are", "what", "does", "with", "on", "is", "a", "an", "by", "as"}
def search_corpus(query, limit=60):
    if not CORPUS_PATH.exists():
        return []
    entries = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["papers"]
    tokens = set(re.findall(r"[a-z0-9]+", query.lower())) - STOP
    ranked = []
    for entry in entries:
        text = entry["title"] + " " + (entry.get("abstract") or "")
        score = len(tokens & set(re.findall(r"[a-z0-9]+", text.lower())))
        if score:
            ranked.append((score, entry))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [PaperSearchResult(**entry) for _, entry in ranked[:limit]]
