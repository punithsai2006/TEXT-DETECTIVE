import os
import re
import uuid
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import DocumentMetadata, DocumentType, TextChunk


# Standard fixed-width sentence boundary split
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\[\(])|(?<=\n)\s*(?=[A-Z0-9\"'\[\(])")
COMMON_ABBREVS = {"mr.", "mrs.", "ms.", "dr.", "prof.", "capt.", "lt.", "sgt.", "vs.", "etc.", "e.g.", "i.e.", "p.m.", "a.m.", "approx.", "dept.", "no.", "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "oct.", "nov.", "dec."}


def normalize_whitespace_and_noise(text: str) -> str:
    """
    Normalizes unicode, carriage returns, and noise while preserving
    meaningful indentation, timestamps, speaker headers, and punctuation.
    """
    if not text:
        return ""
    # Normalize unicode to NFKC
    text = unicodedata.normalize("NFKC", text)
    # Replace CRLF and CR with LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace zero-width characters and odd unicode spaces
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    # Replace non-breaking spaces
    text = text.replace("\u00a0", " ")
    # Replace tabs with spaces
    text = text.replace("\t", "    ")
    # Remove excessive blank lines (more than 2 consecutive newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into source sentences, preserving exact dialogue turns,
    log lines, and structured sentences.
    """
    if not text:
        return []

    # If the text is largely structured line logs (e.g., timestamps at start of lines)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    is_log_or_dialogue = False
    if lines:
        log_match_count = sum(
            1 for line in lines
            if re.match(r"^\[?\d{1,2}:\d{2}(?::\d{2})?\]?", line)
            or re.match(r"^[A-Z0-9_ -]{2,20}:", line)
        )
        if log_match_count / len(lines) > 0.4:
            is_log_or_dialogue = True

    if is_log_or_dialogue:
        return lines

    # Standard narrative text splitting
    raw_sentences = SENTENCE_SPLIT_REGEX.split(text)
    cleaned: List[str] = []
    for s in raw_sentences:
        if not s:
            continue
        s_clean = s.strip()
        if not s_clean:
            continue
        if cleaned:
            last_word = cleaned[-1].split()[-1].lower() if cleaned[-1].split() else ""
            if last_word in COMMON_ABBREVS:
                # Merge with previous sentence
                cleaned[-1] = f"{cleaned[-1]} {s_clean}"
                continue
        cleaned.append(s_clean)
    return cleaned if cleaned else [text.strip()]


def detect_document_type(filename: str, text: str) -> DocumentType:
    fn_lower = filename.lower()
    t_lower = text.lower()[:3000]

    if "interview" in fn_lower or "transcript" in fn_lower or "witness" in fn_lower:
        return DocumentType.INTERVIEW
    if "email" in fn_lower or "memo" in fn_lower or "correspondence" in fn_lower:
        return DocumentType.EMAIL
    if "log" in fn_lower or "access" in fn_lower or "audit" in fn_lower or "badge" in fn_lower:
        return DocumentType.LOG
    if "report" in fn_lower or "forensic" in fn_lower or "incident" in fn_lower:
        return DocumentType.REPORT

    # Content-based heuristics
    if ("from:" in t_lower and "to:" in t_lower) or "subject:" in t_lower or "re:" in t_lower:
        return DocumentType.EMAIL
    if re.search(r"^(?:q:|interviewer:|interviewee:|[A-Z]{2,15}:)", text, re.MULTILINE):
        return DocumentType.INTERVIEW
    if re.search(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}|\[\d{2}:\d{2}:\d{2}\]|STATUS:|INFO:|ERROR:", text, re.MULTILINE):
        return DocumentType.LOG
    if "incident report" in t_lower or "executive summary" in t_lower or "findings:" in t_lower or "investigation" in t_lower:
        return DocumentType.REPORT

    return DocumentType.OTHER


def extract_metadata_heuristics(filename: str, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts speaker/author, timestamp, and description if explicitly present.
    NEVER fabricates metadata: returns None if absent.
    """
    speaker = None
    timestamp = None
    description = None

    # Check for speaker in transcript header or dialogue
    speaker_match = re.search(r"(?:Interviewee|Witness|Subject|Author|Speaker|From):\s*([A-Za-z0-9 .'-]+)", text[:1000], re.IGNORECASE)
    if speaker_match:
        cand = speaker_match.group(1).strip()
        if len(cand) > 1 and len(cand) < 60 and "@" not in cand:
            speaker = cand
        elif "@" in cand:
            speaker = cand.split("<")[0].strip() or cand

    # Check for timestamp in header
    time_match = re.search(r"(?:Date|Timestamp|Time|Occurred):\s*([A-Za-z0-9 :,./-]+)", text[:1000], re.IGNORECASE)
    if time_match:
        timestamp = time_match.group(1).strip()

    # Filename fallback for speaker if filename is e.g. "interview_alice_vance.txt"
    if not speaker:
        fn_parts = Path(filename).stem.replace("-", "_").split("_")
        if len(fn_parts) >= 2 and fn_parts[0].lower() in ["interview", "statement", "witness"]:
            cand = " ".join(p.capitalize() for p in fn_parts[1:])
            speaker = cand

    return speaker, timestamp, description


def extract_text_from_file(file_path: Path, filename: str) -> Tuple[str, Optional[str]]:
    """
    Extracts text from file. Handles .txt, .log, .csv, .json, .pdf, .docx.
    Returns (extracted_text, warning_if_any).
    """
    suffix = Path(filename).suffix.lower()
    warning = None

    if suffix in [".txt", ".log", ".csv", ".json", ".md"]:
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read(), None
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode text file {filename} with supported encodings.")

    elif suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ValueError(f"PDF {filename} is password-protected and cannot be decrypted.")

            pages_text = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages_text.append(page_text)

            full_text = "\n\n".join(pages_text).strip()
            if len(full_text) < 25:
                warning = f"Warning: PDF '{filename}' contains no extractable text. Scanned document detected; OCR is not enabled."
                full_text = f"[UNREADABLE SCANNED PDF: {filename}]"

            return full_text, warning
        except Exception as e:
            if "password" in str(e).lower():
                raise ValueError(f"PDF {filename} is encrypted or password-protected.")
            raise ValueError(f"Failed to parse PDF {filename}: {str(e)}")

    elif suffix in [".docx", ".doc"]:
        try:
            import docx
            doc = docx.Document(str(file_path))
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paras), None
        except Exception as e:
            raise ValueError(f"Failed to parse Word document {filename}: {str(e)}")

    else:
        raise ValueError(f"Unsupported file format '{suffix}' for {filename}. Supported: TXT, PDF, DOCX, CSV, JSON, LOG.")


def chunk_document(
    case_id: str,
    document_id: str,
    filename: str,
    document_type: DocumentType,
    cleaned_text: str,
    speaker: Optional[str] = None,
    timestamp: Optional[str] = None,
    chunk_size_sentences: int = 3,
) -> List[TextChunk]:
    """
    Splits document into semantic chunks of sentences, preserving exact sentence references.
    """
    sentences = split_into_sentences(cleaned_text)
    if not sentences:
        return []

    chunks: List[TextChunk] = []
    current_sentences: List[str] = []
    current_indices: List[int] = []

    char_cursor = 0

    for idx, sentence in enumerate(sentences):
        current_sentences.append(sentence)
        current_indices.append(idx)

        # Chunk threshold reached or at last sentence
        if len(current_sentences) >= chunk_size_sentences or idx == len(sentences) - 1:
            chunk_text = " ".join(current_sentences)
            chunk_id = f"chk_{document_id}_{len(chunks) + 1}"
            char_start = cleaned_text.find(sentence, max(0, char_cursor - 100))
            if char_start == -1:
                char_start = char_cursor
            char_end = char_start + len(chunk_text)
            char_cursor = char_end

            # Extract local speaker if line has explicit Speaker: Prefix
            local_speaker = speaker
            speaker_match = re.match(r"^([A-Z0-9_ -]{2,25}):", current_sentences[0])
            if speaker_match:
                local_speaker = speaker_match.group(1).strip()

            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    case_id=case_id,
                    document_id=document_id,
                    filename=filename,
                    document_type=document_type,
                    speaker=local_speaker,
                    timestamp=timestamp,
                    text=chunk_text,
                    sentence_indices=list(current_indices),
                    char_start=char_start,
                    char_end=char_end,
                )
            )
            current_sentences = []
            current_indices = []

    return chunks


def process_uploaded_file(
    case_id: str,
    file_path: Path,
    original_filename: str,
    override_doc_type: Optional[DocumentType] = None,
    override_speaker: Optional[str] = None,
    override_author: Optional[str] = None,
    override_timestamp: Optional[str] = None,
    override_description: Optional[str] = None,
) -> DocumentMetadata:
    """
    Full Module 1 pipeline for a single file.
    """
    # 1. Validation
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValueError(f"Uploaded file '{original_filename}' is empty (0 bytes).")
    if file_size > 25 * 1024 * 1024:
        raise ValueError(f"Uploaded file '{original_filename}' exceeds the 25MB limit.")

    # 2. Extract raw text
    raw_text, warning = extract_text_from_file(file_path, original_filename)

    # 3. Clean and normalize
    cleaned_text = normalize_whitespace_and_noise(raw_text)

    # 4. Document Type
    doc_type = override_doc_type or detect_document_type(original_filename, cleaned_text)

    # 5. Metadata extraction
    auto_speaker, auto_timestamp, auto_desc = extract_metadata_heuristics(original_filename, cleaned_text)
    speaker = override_speaker or auto_speaker
    author = override_author or (speaker if doc_type in [DocumentType.REPORT, DocumentType.EMAIL] else None)
    timestamp = override_timestamp or auto_timestamp
    description = override_description or auto_desc

    # 6. Chunking
    document_id = f"doc_{uuid.uuid4().hex[:8]}"
    chunks = chunk_document(
        case_id=case_id,
        document_id=document_id,
        filename=original_filename,
        document_type=doc_type,
        cleaned_text=cleaned_text,
        speaker=speaker,
        timestamp=timestamp,
    )

    return DocumentMetadata(
        document_id=document_id,
        case_id=case_id,
        filename=original_filename,
        document_type=doc_type,
        speaker=speaker,
        author=author,
        timestamp=timestamp,
        description=description,
        file_size_bytes=file_size,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        chunks=chunks,
        status="processed",
        warning=warning,
    )
