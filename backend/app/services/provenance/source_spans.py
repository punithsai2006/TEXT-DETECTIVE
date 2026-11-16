"""Offsets are zero-based, end-exclusive Python character offsets in raw_text.

PDF pages are separated by form feed; paragraphs are numbered from 1 per page.
These are extracted-text locations, never invented visual page line numbers.
"""
import hashlib
import re
from app.models.evidence_review import SourceSpan

PARSER_VERSION = "source-spans-v2.1"


def build_source_spans(case_id, document_id, raw_text, content_hash, is_pdf=False):
    version = hashlib.sha256((PARSER_VERSION + content_hash + raw_text).encode()).hexdigest()[:20]
    spans = []
    cursor = 0
    for page, text in enumerate(raw_text.split("\f"), 1):
        # Non-empty paragraphs, including contiguous log lines. Large paragraphs
        # remain intact here; ingestion/run limits are checked explicitly.
        paragraph = 0
        for match in re.finditer(r"\S[\s\S]*?(?=\n[ \t]*\n|\Z)", text):
            end = match.end()
            while end > match.start() and text[end - 1].isspace():
                end -= 1
            quote = text[match.start():end]
            if not quote:
                continue
            paragraph += 1
            start = cursor + match.start()
            span_id = f"sp_{document_id}_{version}_{start}_{cursor + end}"
            spans.append(SourceSpan(
                span_id=span_id, case_id=case_id, document_id=document_id,
                extraction_version=version, quote=quote,
                page_number=page if is_pdf else None, paragraph=paragraph,
                char_start=start, char_end=cursor + end,
            ).model_dump())
        cursor += len(text) + 1
    return version, spans
