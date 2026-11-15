import calendar
from datetime import date, datetime, time, timezone
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

MONTH_NAME_TO_INT = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

TIMEZONE_ABBREVS = {
    "utc": "+00:00",
    "gmt": "+00:00",
    "est": "-05:00",
    "edt": "-04:00",
    "cst": "-06:00",
    "cdt": "-05:00",
    "mst": "-07:00",
    "mdt": "-06:00",
    "pst": "-08:00",
    "pdt": "-07:00",
    "z": "+00:00",
}


def parse_date_string(text: str, default_year: Optional[int] = None) -> Optional[date]:
    """
    Parses date from text supporting:
    - 19 Nov 2026, 19 November 2026, 19-Nov-2026
    - November 19, 2026, Nov 19, 2026, Nov 19 2026
    - 2026-11-19, 2026/11/19
    - 19/11/2026, 19-11-2026
    - ISO 8601 timestamps
    - Day + Month without year (e.g. '21 November', 'Nov 21') if default_year provided
    """
    if not text or len(text.strip()) < 4:
        return None

    clean = text.strip()

    # 1. ISO 8601 or YYYY-MM-DD or YYYY/MM/DD
    m_iso = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", clean)
    if m_iso:
        try:
            year, month, day = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                return date(year, month, day)
        except ValueError:
            pass

    # 2. DD Month YYYY: e.g. "19 Nov 2026", "19 November 2026", "19-Nov-2026"
    m_dmy = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?[\s\-]+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:[\s,]+(\d{4}))?\b",
        clean,
        re.IGNORECASE,
    )
    if m_dmy:
        day = int(m_dmy.group(1))
        m_str = m_dmy.group(2).lower()
        y_str = m_dmy.group(3)
        year = int(y_str) if y_str else default_year
        month = MONTH_NAME_TO_INT.get(m_str)
        if month and year and 1900 <= year <= 2100 and 1 <= day <= 31:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # 3. Month DD, YYYY: e.g. "November 19, 2026", "Nov 19, 2026", "November 19 2026"
    m_mdy = re.search(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s\-]+(\d{1,2})(?:st|nd|rd|th)?(?:,)?(?:[\s]+(\d{4}))?\b",
        clean,
        re.IGNORECASE,
    )
    if m_mdy:
        m_str = m_mdy.group(1).lower()
        day = int(m_mdy.group(2))
        y_str = m_mdy.group(3)
        year = int(y_str) if y_str else default_year
        month = MONTH_NAME_TO_INT.get(m_str)
        if month and year and 1900 <= year <= 2100 and 1 <= day <= 31:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # 4. DD/MM/YYYY or DD-MM-YYYY (e.g. "19/11/2026", "19-11-2026")
    m_num = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", clean)
    if m_num:
        p1, p2, year = int(m_num.group(1)), int(m_num.group(2)), int(m_num.group(3))
        if 1900 <= year <= 2100:
            if 1 <= p2 <= 12 and 1 <= p1 <= 31:
                try:
                    return date(year, p2, p1)
                except ValueError:
                    pass
            if 1 <= p1 <= 12 and 1 <= p2 <= 31:
                try:
                    return date(year, p1, p2)
                except ValueError:
                    pass

    return None


TZ_PATTERN = r"(?:UTC|GMT|EST|EDT|CST|CDT|MST|MDT|PST|PDT|BST|CET|CEST|[+-]\d{2}:?\d{2})"


def parse_time_string(text: str) -> Tuple[Optional[time], Optional[str], Optional[str], str]:
    """
    Parses clock time and timezone from text.
    Returns (parsed_time, raw_time_str, timezone_str, precision).
    Precision: 'second', 'minute', 'approximate', 'none'
    """
    # 1. Approximate time phrases: e.g. "around 03:30 PM", "shortly after 18:00", "about 5:30 pm"
    m_approx = re.search(
        rf"\b(around|about|approximately|shortly before|shortly after)\s+(\d{{1,2}}(?::\d{{2}})?(?::\d{{2}})?\s*(?:AM|PM|am|pm)?(?:\s*{TZ_PATTERN})?)\b",
        text,
        re.IGNORECASE,
    )
    if m_approx:
        raw_phrase = m_approx.group(0).strip()
        time_part = m_approx.group(2).strip()
        t_obj, _, tz, _ = parse_time_string(time_part)
        if t_obj:
            return t_obj, raw_phrase, tz, "approximate"

    # 2. Standard 24h or 12h time with seconds: e.g. "09:02:15", "18:16:33", "09:02:15 PM"
    m_sec = re.search(
        rf"\b(\d{{1,2}}):(\d{{2}}):(\d{{2}})\s*(AM|PM|am|pm)?(?:\s*({TZ_PATTERN}))?\b",
        text,
    )
    if m_sec:
        h, m, s = int(m_sec.group(1)), int(m_sec.group(2)), int(m_sec.group(3))
        ampm = m_sec.group(4)
        tz = m_sec.group(5)
        if ampm:
            ampm_up = ampm.upper()
            if ampm_up == "PM" and h < 12:
                h += 12
            elif ampm_up == "AM" and h == 12:
                h = 0
        if 0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59:
            return time(h, m, s), m_sec.group(0).strip(), tz, "second"

    # 3. Bracketed or standard hours:minutes: e.g. "[10:15 AM]", "09:14 PM", "17:30", "08:05 AM"
    m_min = re.search(
        rf"(?:\[|\b)(\d{{1,2}}):(\d{{2}})\s*(AM|PM|am|pm)?(?:\s*({TZ_PATTERN}))?(?:\]|\b)",
        text,
    )
    if m_min:
        h, m = int(m_min.group(1)), int(m_min.group(2))
        ampm = m_min.group(3)
        tz = m_min.group(4)
        if ampm:
            ampm_up = ampm.upper()
            if ampm_up == "PM" and h < 12:
                h += 12
            elif ampm_up == "AM" and h == 12:
                h = 0
        if 0 <= h <= 23 and 0 <= m <= 59:
            return time(h, m, 0), m_min.group(0).strip("[] "), tz, "minute"

    return None, None, None, "none"


def extract_document_header_datetime(document_text: str) -> Tuple[Optional[date], Optional[time], Optional[str]]:
    """
    Scans document header for date and time.
    Returns (header_date, header_time, timezone_str).
    """
    lines = [ln.strip() for ln in document_text[:2500].split("\n") if ln.strip()]
    h_date = None
    h_time = None
    h_tz = None

    for ln in lines[:30]:
        # Date patterns
        if not h_date:
            m_header = re.search(
                r"^(?:Date(?:\s+of\s+interview)?|Interview\s+date|Review\s+date|Investigation\s+date|Incident\s+date|Occurred|Date/Time):\s*(.+)$",
                ln,
                re.IGNORECASE,
            )
            if m_header:
                h_date = parse_date_string(m_header.group(1))

            m_colon = re.search(r"\bDATE:\s*([A-Za-z0-9\s,./-]+)", ln, re.IGNORECASE)
            if m_colon and not h_date:
                h_date = parse_date_string(m_colon.group(1))

        # Time patterns on separate line, e.g. "Time: 09:14 PM"
        if not h_time:
            m_time_hdr = re.search(r"^(?:Time):\s*([0-9:AMPamp\s]+(?:\s*[A-Za-z]{2,4})?)", ln, re.IGNORECASE)
            if m_time_hdr:
                t_val, _, tz_val, _ = parse_time_string(m_time_hdr.group(1))
                if t_val:
                    h_time = t_val
                    h_tz = tz_val

    return h_date, h_time, h_tz


def extract_document_header_date(document_text: str) -> Optional[date]:
    d, _, _ = extract_document_header_datetime(document_text)
    return d


class ParsedEventTimestamp:
    def __init__(
        self,
        dt: Optional[datetime],
        display_str: str,
        precision: str,
        confidence: float,
        is_date_inferred: bool,
        raw_text: Optional[str] = None,
        timezone_str: Optional[str] = None,
    ):
        self.dt = dt
        self.display_str = display_str
        self.precision = precision
        self.confidence = confidence
        self.is_date_inferred = is_date_inferred
        self.raw_text = raw_text
        self.timezone_str = timezone_str

    @property
    def sort_key(self) -> str:
        if self.dt:
            return self.dt.strftime("%Y%m%d%H%M%S")
        return "99999999999999"

    @property
    def parsed_date_iso(self) -> Optional[str]:
        return self.dt.strftime("%Y-%m-%d") if self.dt else None

    @property
    def parsed_time_iso(self) -> Optional[str]:
        return self.dt.strftime("%H:%M:%S") if self.dt else None

    @property
    def parsed_timestamp_iso(self) -> Optional[str]:
        return self.dt.isoformat() if self.dt else None


def resolve_sentence_timestamp(
    sentence: str,
    doc_header_date: Optional[date],
    current_context_date: Optional[date],
    doc_type: str = "other",
) -> Tuple[ParsedEventTimestamp, Optional[date]]:
    """
    Parses timestamp from sentence using contextual resolution:
    1. Checks if sentence has an explicit date (e.g. 'on Saturday, 21 November', '19 November 2026').
       Updates context_date if found.
    2. Parses clock time.
    3. Resolves date from sentence explicit date -> current context date -> document header date.
    4. Does NOT invent a date if no date context exists.
    Returns (ParsedEventTimestamp, updated_context_date).
    """
    default_yr = current_context_date.year if current_context_date else (doc_header_date.year if doc_header_date else None)
    explicit_date = parse_date_string(sentence, default_year=default_yr)
    new_context_date = explicit_date or current_context_date

    # Parse time component
    parsed_t, raw_t, tz_str, precision = parse_time_string(sentence)

    if explicit_date and parsed_t:
        dt = datetime.combine(explicit_date, parsed_t)
        disp = dt.strftime("%Y-%m-%d %H:%M:%S")
        m_combined = re.search(
            r"\b\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}(?::\d{2})?\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\b",
            sentence,
        )
        combined_raw = m_combined.group(0) if m_combined else (f"{explicit_date.isoformat()} {raw_t}" if raw_t else disp)
        return (
            ParsedEventTimestamp(
                dt=dt,
                display_str=disp,
                precision=precision,
                confidence=1.0,
                is_date_inferred=False,
                raw_text=combined_raw,
                timezone_str=tz_str,
            ),
            new_context_date,
        )

    if parsed_t:
        # We have time, but date must be resolved contextually
        target_date = current_context_date or doc_header_date
        if target_date:
            dt = datetime.combine(target_date, parsed_t)
            disp = dt.strftime("%Y-%m-%d %H:%M:%S")
            return (
                ParsedEventTimestamp(
                    dt=dt,
                    display_str=disp,
                    precision=precision,
                    confidence=0.9 if current_context_date else 0.8,
                    is_date_inferred=True,
                    raw_text=raw_t or sentence,
                    timezone_str=tz_str,
                ),
                new_context_date,
            )
        else:
            # Time is known, but date is completely unknown. Do NOT invent a date.
            disp = f"{raw_t} (Date unspecified)"
            return (
                ParsedEventTimestamp(
                    dt=None,
                    display_str=disp,
                    precision=precision,
                    confidence=0.4,
                    is_date_inferred=False,
                    raw_text=raw_t,
                    timezone_str=tz_str,
                ),
                new_context_date,
            )

    if explicit_date:
        # Date is known, time is unspecified
        dt = datetime.combine(explicit_date, time(0, 0, 0))
        disp = f"{explicit_date.isoformat()} (Time unspecified)"
        return (
            ParsedEventTimestamp(
                dt=dt,
                display_str=disp,
                precision="day",
                confidence=0.9,
                is_date_inferred=False,
                raw_text=sentence,
                timezone_str=None,
            ),
            new_context_date,
        )

    # Neither time nor date found
    return (
        ParsedEventTimestamp(
            dt=None,
            display_str="Time unspecified",
            precision="none",
            confidence=0.0,
            is_date_inferred=False,
            raw_text=None,
            timezone_str=None,
        ),
        new_context_date,
    )
