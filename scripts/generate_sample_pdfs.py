#!/usr/bin/env python3
"""
Generate realistic sample PDF documents for Text Detective investigations.
Produces standard PDF 1.4 documents formatted with headers, timestamps, and multi-page layout.
"""

import io
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_pdf_bytes(lines_list: list[str], title: str = "Investigation Document") -> bytes:
    """Create a standard PDF 1.4 binary stream with multi-page support."""
    PAGE_SIZE = 42
    # Ensure lines fit within width (approx 80 chars per line)
    wrapped_lines = []
    for raw_line in lines_list:
        if not raw_line.strip():
            wrapped_lines.append("")
            continue
        # Simple word wrap
        words = raw_line.split(" ")
        current_line = []
        current_len = 0
        for w in words:
            if current_len + len(w) + 1 > 78:
                wrapped_lines.append(" ".join(current_line))
                current_line = [w]
                current_len = len(w)
            else:
                current_line.append(w)
                current_len += len(w) + 1
        if current_line:
            wrapped_lines.append(" ".join(current_line))

    pages_lines = [
        wrapped_lines[i : i + PAGE_SIZE]
        for i in range(0, max(len(wrapped_lines), 1), PAGE_SIZE)
    ]
    num_pages = len(pages_lines)

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")

    objs = {}
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids_str = " ".join(f"{4 + 2 * i} 0 R" for i in range(num_pages))
    objs[2] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode("latin-1")
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    for i, page_lines in enumerate(pages_lines):
        page_idx = 4 + 2 * i
        content_idx = 5 + 2 * i

        objs[page_idx] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_idx} 0 R >>"
        ).encode("latin-1")

        text_ops = ["BT", "/F1 10 Tf", "50 730 Td", "14 TL"]
        if i == 0:
            text_ops.append(f"({title.upper()}) Tj T*")
            text_ops.append(f"(CONFIDENTIAL // FORENSIC INVESTIGATION RECORD) Tj T*")
            text_ops.append("() Tj T*")

        for line in page_lines:
            escaped = (
                line.replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
            )
            text_ops.append(f"({escaped}) Tj T*")

        # Page footer
        text_ops.append("() Tj T*")
        text_ops.append(f"(--- Page {i + 1} of {num_pages} ---) Tj T*")
        text_ops.append("ET")

        content_stream = "\n".join(text_ops).encode("latin-1", errors="replace")
        objs[content_idx] = (
            f"<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1")
            + content_stream
            + b"\nendstream"
        )

    xref_offsets = {}
    for obj_id in sorted(objs.keys()):
        xref_offsets[obj_id] = out.tell()
        out.write(f"{obj_id} 0 obj\n".encode("latin-1"))
        out.write(objs[obj_id])
        out.write(b"\nendobj\n")

    xref_pos = out.tell()
    total_objs = len(objs)
    out.write(f"xref\n0 {total_objs + 1}\n".encode("latin-1"))
    out.write(b"0000000000 65535 f \n")
    for obj_id in range(1, total_objs + 1):
        out.write(f"{xref_offsets[obj_id]:010d} 00000 n \n".encode("latin-1"))

    out.write(
        f"trailer\n<< /Size {total_objs + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode(
            "latin-1"
        )
    )

    return out.getvalue()


SAMPLE_CASES_DIR = PROJECT_ROOT / "data" / "sample_cases"
OUTPUT_PDF_DIR = PROJECT_ROOT / "data" / "sample_pdfs"


def generate_sample_pdfs():
    OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    # 1. Incident Report PDF
    doc1 = [
        "INCIDENT OVERVIEW:",
        "On October 12, 2024, at approximately 21:15 UTC, the Security Operations Center (SOC) detected an anomalous outbound SFTP transmission originating from database server DB-PROD-02 located inside Server Room B.",
        "Total exfiltrated volume: 14.8 Gigabytes containing 420,000 customer profile records, encrypted salted credential hashes, and internal billing routing numbers.",
        "The automated network threshold alert fired at 21:18 UTC when outbound throughput exceeded 120 Mbps to an external unlisted IP address (198.51.100.42).",
        "",
        "PRELIMINARY SUSPECTS & PERSONS OF INTEREST:",
        "- Frank Miller: Senior Database Administrator. Possesses unrestricted sudo privileges on DB-PROD-02. Scheduled on-call shift.",
        "- Alice Vance: Lead Infrastructure Engineer. Holds root infrastructure SSH keys and physical server room access badge.",
        "- Bob Chen: Network Operations Specialist. Responsible for firewall configuration rules and port 22 SFTP routing.",
        "",
        "INVESTIGATION MANDATE:",
        "1. Reconstruct exact chronological sequence of physical access, authentication sessions, and file staging.",
        "2. Cross-reference witness interview alibis against physical telemetry and digital system event logs.",
        "3. Evaluate competing hypotheses regarding insider exfiltration versus compromised external credentials.",
    ]
    p1 = OUTPUT_PDF_DIR / "01_security_incident_report.pdf"
    p1.write_bytes(create_pdf_bytes(doc1, "Security Incident Report - Case 2024-082"))
    generated.append(p1)

    # 2. Suspect Interview PDF (Frank Miller - False Alibi)
    doc2 = [
        "WITNESS / SUSPECT INTERVIEW TRANSCRIPT:",
        "Date: October 13, 2024 | Time: 09:30 UTC",
        "Interviewer: Detective Sarah Jenkins (Corporate Forensic Investigations)",
        "Interviewee: Frank Miller (Senior DBA, Employee ID: EMP-4091)",
        "",
        "EXCERPT OF RELEVANT TESTIMONY:",
        "Jenkins: Can you state your whereabouts on the evening of October 12, 2024, between 19:00 and 23:00?",
        "Frank Miller: Yes, absolutely. I wrapped up my routine database indexing tasks around 19:45.",
        "Frank Miller: I had an early dinner planned with my brother. I packed my laptop and left the office premises precisely at 20:00.",
        "Jenkins: Did you return to the building or access the company network remotely later that night?",
        "Frank Miller: No, definitely not. I was at dinner at Osteria Morini until 22:30. My phone battery died around 20:30, so I had no network connectivity until I returned home after 23:00.",
        "Jenkins: Did you share your administrative credentials or MFA hardware token with anyone on your team?",
        "Frank Miller: Never. My YubiKey hardware token remained attached to my keychain at all times.",
        "",
        "INVESTIGATOR NOTE:",
        "Subject displayed elevated anxiety when questioned regarding remote SFTP staging scripts.",
    ]
    p2 = OUTPUT_PDF_DIR / "02_interview_frank_miller.pdf"
    p2.write_bytes(create_pdf_bytes(doc2, "Interview Transcript - Frank Miller"))
    generated.append(p2)

    # 3. Server Access Logs PDF (Contradicts Alibi)
    doc3 = [
        "SYSTEM ACCESS AUDIT LOG DUMP:",
        "System: DB-PROD-02.internal.meridian.net",
        "Log Source: /var/log/secure and /var/log/audit/audit.log",
        "Time Range: 2024-10-12 20:00:00 UTC to 2024-10-12 22:00:00 UTC",
        "",
        "EVENT ENTRIES:",
        "[2024-10-12 20:14:12] sshd[14820]: Accepted publickey for fmiller from 10.0.4.150 port 54102 ssh2: RSA SHA256:d8a9e",
        "[2024-10-12 20:15:01] sudo[14892]: fmiller : TTY=pts/2 ; PWD=/home/fmiller ; USER=root ; COMMAND=/bin/bash",
        "[2024-10-12 20:42:30] postgres[15011]: [3-1] user=postgres,db=customer_master LOG: statement: COPY customers TO '/tmp/cust_export_20241012.tar.gz' WITH BINARY",
        "[2024-10-12 20:45:18] sftp-server[15120]: session opened for local user fmiller from 10.0.4.150",
        "[2024-10-12 20:45:55] sftp-server[15120]: sent /tmp/cust_export_20241012.tar.gz (14,812,410 bytes) to remote destination 198.51.100.42",
        "[2024-10-12 21:05:40] sshd[14820]: session closed for user fmiller",
        "",
        "FORENSIC SUMMARY:",
        "Session authenticated using Frank Miller's hardware MFA key and private SSH certificate at 20:45 UTC, directly while subject claimed to be offsite without connectivity.",
    ]
    p3 = OUTPUT_PDF_DIR / "03_server_access_logs.pdf"
    p3.write_bytes(create_pdf_bytes(doc3, "System Audit Logs - DB-PROD-02"))
    generated.append(p3)

    # 4. RFID Badge Telemetry PDF (Contradicts Claim of Leaving at 20:00)
    doc4 = [
        "PHYSICAL SECURITY TELEMETRY - ACCESS CONTROL SYSTEM:",
        "Facility: Meridian Technology Center - Building 4",
        "Controller: HID Aero Network Access Controller V1000",
        "Report Generated: 2024-10-13 08:00:00 UTC",
        "",
        "BADGE EVENT RECORDS (CARD #88219 - ASSIGNED TO: FRANK MILLER):",
        "1. 2024-10-12 08:45:22 - Turnstile Main Lobby [ENTRY] - VALID ACCESS GRANTED",
        "2. 2024-10-12 12:15:04 - Turnstile Main Lobby [EXIT] - VALID ACCESS GRANTED",
        "3. 2024-10-12 13:02:18 - Turnstile Main Lobby [ENTRY] - VALID ACCESS GRANTED",
        "4. 2024-10-12 20:10:45 - Server Room B Secure Airlock [ENTRY] - VALID ACCESS GRANTED",
        "5. 2024-10-12 21:40:12 - Server Room B Secure Airlock [EXIT] - VALID ACCESS GRANTED",
        "6. 2024-10-12 21:45:08 - Turnstile Main Lobby [EXIT] - VALID ACCESS GRANTED",
        "",
        "PHYSICAL CONTRADICTION FINDING:",
        "Frank Miller testified he exited the facility at 20:00:00 UTC.",
        "Badge scan confirms Frank Miller entered Server Room B at 20:10:45 UTC and exited the main turnstile at 21:45:08 UTC.",
    ]
    p4 = OUTPUT_PDF_DIR / "04_rfid_badge_telemetry.pdf"
    p4.write_bytes(create_pdf_bytes(doc4, "Building Access Telemetry - RFID Logs"))
    generated.append(p4)

    # 5. Financial Wire & Shell Company Memo PDF
    doc5 = [
        "FINANCIAL INTELLIGENCE MEMORANDUM:",
        "To: Forensic Audit Division",
        "From: Anti-Money Laundering & Compliance Unit",
        "Date: October 14, 2024",
        "Subject: Suspicious Wire Activity - Account Linked to Meridian Personnel",
        "",
        "TRANSACTION DETAILS:",
        "- Beneficiary Entity: NexaFlow Consulting Ltd. (Registered: Seychelles)",
        "- Beneficial Owner: Frank Miller (100% shareholding via trust deed)",
        "- Amount: $85,000.00 USD",
        "- Originating Bank: CypherSec Holdings (Zurich, CH)",
        "- Date / Time: 2024-10-12 22:15:00 UTC",
        "- Memo Reference: 'Contract milestone delivery - Phase 3 Data Asset'",
        "",
        "ANALYSIS:",
        "The wire transfer was initiated exactly 30 minutes after the SFTP exfiltration of the customer database completed.",
        "Corroborates intentional financial incentive and deliberate data exfiltration hypothesis.",
    ]
    p5 = OUTPUT_PDF_DIR / "05_financial_wire_memo.pdf"
    p5.write_bytes(create_pdf_bytes(doc5, "Financial Intelligence Audit Memo"))
    generated.append(p5)

    print(f"Successfully generated {len(generated)} PDF sample files in: {OUTPUT_PDF_DIR}")
    for p in generated:
        print(f" - {p.name} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    generate_sample_pdfs()
