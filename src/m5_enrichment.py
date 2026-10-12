from __future__ import annotations

"""
Module 5: Enrichment Pipeline
==============================
Làm giàu chunks TRƯỚC khi embed: Summarize, HyQA, Contextual Prepend, Auto Metadata.

Test: pytest tests/test_m5.py
"""

import os, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY


@dataclass
class EnrichedChunk:
    """Chunk đã được làm giàu."""
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str  # "contextual", "summary", "hyqa", "full"


# ─── Technique 1: Chunk Summarization ────────────────────


def summarize_chunk(text: str) -> str:
    """
    Tạo summary ngắn cho chunk.
    Embed summary thay vì (hoặc cùng với) raw chunk → giảm noise.
    """
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Tóm tắt đoạn văn sau trong 2-3 câu ngắn gọn bằng tiếng Việt."},
                    {"role": "user", "content": text},
                ],
                max_tokens=150,
            )
            content = resp.choices[0].message.content.strip()
            if content:
                return content
        except Exception as e:
            print(f"  ⚠️  OpenAI summarize failed: {e}")

    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    return ". ".join(sentences[:2]) + ("." if sentences and not sentences[0].endswith(".") else "") if sentences else text


# ─── Technique 2: Hypothesis Question-Answer (HyQA) ─────


def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    """
    Generate câu hỏi mà chunk có thể trả lời.
    Index cả questions lẫn chunk → query match tốt hơn (bridge vocabulary gap).
    """
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": f"Dựa trên đoạn văn, tạo {n_questions} câu hỏi mà đoạn văn có thể trả lời. Trả về mỗi câu hỏi trên 1 dòng."},
                    {"role": "user", "content": text},
                ],
                max_tokens=200,
            )
            raw = resp.choices[0].message.content.strip().split("\n")
            cleaned = [q.strip().lstrip("0123456789.-) ") for q in raw if q.strip()]
            if cleaned:
                return cleaned[:n_questions]
        except Exception as e:
            print(f"  ⚠️  OpenAI HyQA failed: {e}")

    import re
    sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if len(s.strip()) > 10]
    return [f"{s.rstrip('.')}?" for s in sentences[:n_questions]]


# ─── Technique 3: Contextual Prepend (Anthropic style) ──


def contextual_prepend(text: str, document_title: str = "") -> str:
    """
    Prepend context giải thích chunk nằm ở đâu trong document.
    Anthropic benchmark: giảm 49% retrieval failure (alone).
    """
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Viết 1 câu ngắn mô tả đoạn văn này nằm ở đâu trong tài liệu và nói về chủ đề gì. Chỉ trả về 1 câu."},
                    {"role": "user", "content": f"Tài liệu: {document_title}\n\nĐoạn văn:\n{text}"},
                ],
                max_tokens=80,
            )
            context = resp.choices[0].message.content.strip()
            if context:
                return f"{context}\n\n{text}"
        except Exception as e:
            print(f"  ⚠️  OpenAI contextual failed: {e}")

    prefix = f"Trích từ {document_title}. " if document_title else ""
    return f"{prefix}{text}"


# ─── Technique 4: Auto Metadata Extraction ──────────────


def extract_metadata(text: str) -> dict:
    """
    LLM extract metadata tự động: topic, entities, date_range, category.
    """
    if OPENAI_API_KEY:
        try:
            import json as _json
            import re as _re
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": 'Trích xuất metadata từ đoạn văn. Trả về JSON: {"topic": "...", "entities": ["..."], "category": "policy|hr|it|finance", "language": "vi|en"}'},
                    {"role": "user", "content": text},
                ],
                max_tokens=150,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = _re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=_re.MULTILINE).strip()
            return _json.loads(raw)
        except Exception as e:
            print(f"  ⚠️  OpenAI metadata failed: {e}")

    topic = "policy"
    lower_t = text.lower()
    if any(w in lower_t for w in ["mật khẩu", "vpn", "bảo mật", "mã hóa"]):
        topic = "it"
    elif any(w in lower_t for w in ["lương", "phép", "thưởng", "thử việc", "bảo hiểm"]):
        topic = "hr"
    elif any(w in lower_t for w in ["chi phí", "tạm ứng", "ngân sách", "bctc"]):
        topic = "finance"
    return {"topic": topic, "entities": [], "category": topic, "language": "vi"}


# ─── Combined Single-Call Mode ───────────────────────────


_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", ".enrichment_cache.json")
_ENRICHMENT_CACHE: dict[str, dict] | None = None


def _get_cache() -> dict[str, dict]:
    global _ENRICHMENT_CACHE
    if _ENRICHMENT_CACHE is None:
        if os.path.exists(_CACHE_PATH):
            try:
                import json as _json
                with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                    _ENRICHMENT_CACHE = _json.load(f)
            except Exception:
                _ENRICHMENT_CACHE = {}
        else:
            _ENRICHMENT_CACHE = {}
    return _ENRICHMENT_CACHE


def _persist_cache():
    if _ENRICHMENT_CACHE is not None:
        try:
            import json as _json
            os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
            with open(_CACHE_PATH, "w", encoding="utf-8") as f:
                _json.dump(_ENRICHMENT_CACHE, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _enrich_single_call(text: str, source: str) -> dict:
    """Single LLM call to get summary + questions + context + metadata.

    ⚠️ Cost optimization: 1 API call thay vì 4 calls riêng lẻ.
    """
    cache = _get_cache()
    cache_key = f"{source}:{text}"
    if cache_key in cache:
        return cache[cache_key]

    if OPENAI_API_KEY:
        try:
            import json as _json
            import re as _re
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": """Phân tích đoạn văn và trả về định dạng JSON hợp lệ (không kèm bất kỳ văn bản giải thích nào khác):
{
  "summary": "tóm tắt 2-3 câu ngắn gọn",
  "questions": ["câu hỏi 1", "câu hỏi 2", "câu hỏi 3"],
  "context": "1 câu mô tả đoạn văn nằm ở đâu trong tài liệu",
  "metadata": {"topic": "...", "entities": ["..."], "category": "policy|hr|it|finance", "language": "vi"}
}"""},
                    {"role": "user", "content": f"Tài liệu: {source}\n\nĐoạn văn:\n{text}"},
                ],
                max_tokens=400,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = _re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=_re.MULTILINE).strip()
            parsed = _json.loads(raw)
            if isinstance(parsed, dict):
                cache[cache_key] = parsed
                _persist_cache()
                return parsed
        except Exception as e:
            print(f"  ⚠️  Enrichment API failed: {e}")

    summary = summarize_chunk(text)
    questions = generate_hypothesis_questions(text)
    context = f"Trích từ tài liệu {source}." if source else ""
    metadata = extract_metadata(text)
    fallback_result = {
        "summary": summary,
        "questions": questions,
        "context": context,
        "metadata": metadata
    }
    cache[cache_key] = fallback_result
    _persist_cache()
    return fallback_result


# ─── Full Enrichment Pipeline ────────────────────────────


def enrich_chunks(
    chunks: list[dict],
    methods: list[str] | None = None,
) -> list[EnrichedChunk]:
    """
    Chạy enrichment pipeline trên danh sách chunks. (Đã implement sẵn — dùng functions ở trên)

    Có 2 chế độ:
    - methods cụ thể (["summary"], ["contextual"]...): gọi từng function riêng (tốt cho học/debug)
    - methods=["combined"] hoặc None: 1 API call duy nhất cho tất cả (tốt cho production)

    Args:
        chunks: List of {"text": str, "metadata": dict}
        methods: Default None → combined mode (1 call/chunk).
                 Options: "summary", "hyqa", "contextual", "metadata", "combined"
    """
    if methods is None:
        methods = ["combined"]

    use_combined = "combined" in methods

    if use_combined and len(chunks) > 1:
        from concurrent.futures import ThreadPoolExecutor

        def _process_one(item: tuple[int, dict]) -> tuple[int, EnrichedChunk]:
            i, chunk = item
            text = chunk["text"]
            source = chunk.get("metadata", {}).get("source", "")
            result = _enrich_single_call(text, source)
            summary = result.get("summary", "")
            questions = result.get("questions", [])
            context_line = result.get("context", "")
            enriched_text = f"{context_line}\n\n{text}" if context_line else text
            auto_meta = result.get("metadata", {})
            return i, EnrichedChunk(
                original_text=text,
                enriched_text=enriched_text,
                summary=summary,
                hypothesis_questions=questions,
                auto_metadata={**chunk.get("metadata", {}), **auto_meta},
                method="+".join(methods),
            )

        enriched_indexed = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for idx, res in enumerate(executor.map(_process_one, enumerate(chunks))):
                enriched_indexed.append(res)
                if (idx + 1) % 10 == 0 or (idx + 1) == len(chunks):
                    print(f"  Enriched {idx + 1}/{len(chunks)} chunks...", flush=True)

        enriched_indexed.sort(key=lambda x: x[0])
        return [item[1] for item in enriched_indexed]

    enriched = []
    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        source = chunk.get("metadata", {}).get("source", "")

        if use_combined:
            result = _enrich_single_call(text, source)
            summary = result.get("summary", "")
            questions = result.get("questions", [])
            context_line = result.get("context", "")
            enriched_text = f"{context_line}\n\n{text}" if context_line else text
            auto_meta = result.get("metadata", {})
        else:
            summary = summarize_chunk(text) if "summary" in methods else ""
            questions = generate_hypothesis_questions(text) if "hyqa" in methods else []
            enriched_text = contextual_prepend(text, source) if "contextual" in methods else text
            auto_meta = extract_metadata(text) if "metadata" in methods else {}

        enriched.append(EnrichedChunk(
            original_text=text,
            enriched_text=enriched_text,
            summary=summary,
            hypothesis_questions=questions,
            auto_metadata={**chunk.get("metadata", {}), **auto_meta},
            method="+".join(methods),
        ))

        if (i + 1) % 10 == 0 or (i + 1) == len(chunks):
            print(f"  Enriched {i + 1}/{len(chunks)} chunks...", flush=True)

    return enriched


# ─── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    sample = "Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm. Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác."

    print("=== Enrichment Pipeline Demo ===\n")
    print(f"Original: {sample}\n")

    s = summarize_chunk(sample)
    print(f"Summary: {s}\n")

    qs = generate_hypothesis_questions(sample)
    print(f"HyQA questions: {qs}\n")

    ctx = contextual_prepend(sample, "Sổ tay nhân viên VinUni 2024")
    print(f"Contextual: {ctx}\n")

    meta = extract_metadata(sample)
    print(f"Auto metadata: {meta}")
