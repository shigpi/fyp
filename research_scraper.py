#!/usr/bin/env python3
"""
VoiceScribe FYP - Research Scraper
===================================
Searches ArXiv and Semantic Scholar for relevant academic papers and
documentation, downloads real PDFs where available, and generates
formatted summary PDFs for web documentation pages. Organises all
output under fyp_documentation/01 Project Artifacts/.

Usage:
    python3 research_scraper.py

Dependencies:
    pip install fpdf2 requests
"""

import os
import time
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent / "fyp_documentation" / "01 Project Artifacts"

METADATA_FILE = BASE_DIR / "research_metadata.json"

# Colour palette for PDFs
COLOUR_BG       = (10,  10,  10)   # near-black
COLOUR_CARD     = (23,  23,  23)   # dark card
COLOUR_ACCENT   = (99,  102, 241)  # indigo
COLOUR_HEADING  = (255, 255, 255)  # white
COLOUR_BODY     = (212, 212, 212)  # light grey
COLOUR_MUTED    = (115, 115, 115)  # muted grey
COLOUR_BORDER   = (38,  38,  38)   # subtle border

# ─────────────────────────────────────────────────────────────────────────────
# Research topics → output paths
# ─────────────────────────────────────────────────────────────────────────────

RESEARCH_TOPICS = [

    # ── 1. Project Initiation ─────────────────────────────────────────────────
    {
        "section": "1. Project Initiation",
        "folder":  "1. Project Initiation/Project Research/Research Papers",
        "papers": [
            {
                "title": "Speech Recognition for Low-Resource Languages — A Survey",
                "query": "speech recognition low resource language neural network",
                "filename": "Speech Recognition Low Resource Languages Survey.pdf",
                "source": "arxiv",
            },
            {
                "title": "Deep Learning Based Speech-to-Text Systems in South Asian Languages",
                "query": "nepali speech recognition deep learning transcription",
                "filename": "Speech To Text South Asian Languages.pdf",
                "source": "arxiv",
            },
            {
                "title": "Multilingual Transcription Systems - State of the Art Review",
                "query": "multilingual automatic speech recognition survey 2023",
                "filename": "Multilingual Transcription State of the Art.pdf",
                "source": "arxiv",
            },
            {
                "title": "End-to-End Nepali Speech Recognition System (Joshi et al., 2023)",
                "query": "end to end Nepali speech recognition system journal 2023",
                "filename": "End to End Nepali ASR Joshi 2023.pdf",
                "source": "arxiv",
            },
            {
                "title": "Aksharantar Dataset - Transliteration for Indian Languages",
                "query": "Aksharantar dataset transliteration Indian languages Devanagari Roman",
                "filename": "Aksharantar Transliteration Dataset.pdf",
                "source": "arxiv",
            },
        ],
    },
    {
        "section": "1. Project Initiation — Tech Stack",
        "folder":  "1. Project Initiation/Research on Tech Stack and Methodology/Research Papers",
        "papers": [
            {
                "title": "Agile Software Development — Methodologies and Trends",
                "query": "agile software development methodology scrum kanban review",
                "filename": "Agile Software Development Methodologies and Trends.pdf",
                "source": "arxiv",
            },
            {
                "title": "FastAPI — Modern Python Web Framework",
                "query": "FastAPI python REST API web framework performance",
                "filename": "FastAPI Python Web Framework.pdf",
                "source": "summary",
                "summary_url": "https://fastapi.tiangolo.com",
                "abstract": (
                    "FastAPI is a modern, fast (high-performance) web framework for building "
                    "APIs with Python 3.8+ based on standard Python type hints. It achieves "
                    "very high performance on par with NodeJS and Go, thanks to Starlette for "
                    "the web parts and Pydantic for the data parts. Key features include: "
                    "automatic interactive API documentation (via Swagger UI), full async "
                    "support, dependency injection, OAuth2/JWT authentication helpers, and "
                    "automatic data validation via Pydantic models. FastAPI is used in the "
                    "VoiceScribe backend for all REST endpoints, middleware, and lifespan "
                    "management of AI model loading."
                ),
            },
            {
                "title": "Flutter Cross-Platform Mobile Development Framework",
                "query": "flutter dart cross platform mobile development architecture",
                "filename": "Flutter Cross Platform Architecture.pdf",
                "source": "arxiv",
            },
            {
                "title": "Scrum Development Process and Guide",
                "query": "scrum agile sprint retrospective planning methodology",
                "filename": "Scrum Development Process and Guide.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── 2. Project Planning ───────────────────────────────────────────────────
    {
        "section": "2. Project Planning",
        "folder":  "2. Project Planning/Research Papers",
        "papers": [
            {
                "title": "Product Backlog Management in Agile Projects",
                "query": "product backlog agile user story sprint planning",
                "filename": "Product Backlog Guide.pdf",
                "source": "arxiv",
            },
            {
                "title": "Software Requirements Specification — Best Practices",
                "query": "software requirements specification SRS IEEE standard",
                "filename": "SRS Documentation Best Practices.pdf",
                "source": "arxiv",
            },
            {
                "title": "Risk Assessment in Software Development Projects",
                "query": "software project risk analysis contingency planning",
                "filename": "Risk Assessment in Software Projects.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── 3. System Design ──────────────────────────────────────────────────────
    {
        "section": "3. System Design",
        "folder":  "3. System Design/Research Papers",
        "papers": [
            {
                "title": "Entity-Relationship Modelling Principles",
                "query": "entity relationship diagram database design relational model",
                "filename": "ERD Design Guide.pdf",
                "source": "arxiv",
            },
            {
                "title": "RESTful API Design Principles and Best Practices",
                "query": "RESTful API design best practices OpenAPI HTTP",
                "filename": "RESTful API Design Principles.pdf",
                "source": "arxiv",
            },
            {
                "title": "PostgreSQL Architecture and Query Optimisation",
                "query": "PostgreSQL relational database architecture performance",
                "filename": "PostgreSQL Architecture.pdf",
                "source": "arxiv",
            },
            {
                "title": "Microservices and Service-Oriented Architecture Patterns",
                "query": "microservices service oriented architecture SOA design",
                "filename": "System Architecture Patterns.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── Sprint 1 — Foundation and Authentication ──────────────────────────────
    {
        "section": "Sprint 1 — Foundation and Authentication",
        "folder":  "4. System Development/Sprint 1 - Foundation and Authentication/Sprint Execution/Research Papers",
        "papers": [
            {
                "title": "JWT Authentication — JSON Web Tokens in REST APIs",
                "query": "JSON web token JWT authentication authorization REST API",
                "filename": "JWT Authentication in REST APIs.pdf",
                "source": "arxiv",
            },
            {
                "title": "RS256 Asymmetric Signing — Security Advantages Over HS256",
                "query": "RSA asymmetric JWT RS256 HS256 token signing security",
                "filename": "RS256 Asymmetric JWT Signing.pdf",
                "source": "summary",
                "summary_url": "https://auth0.com/blog/rs256-vs-hs256/",
                "abstract": (
                    "RS256 (RSA Signature with SHA-256) is an asymmetric algorithm that uses "
                    "a public/private RSA key pair. The server uses the private key to sign "
                    "tokens; any service holding the public key can verify them without "
                    "needing the signing secret. Advantages over HS256 (HMAC-SHA256): "
                    "(1) Secret-less verification — microservices only need the public key, "
                    "reducing the blast radius of a key leak; (2) Non-repudiation — the "
                    "private key holder is the sole token issuer; (3) PKI compatibility — "
                    "keys fit into standard certificate infrastructure. VoiceScribe migrated "
                    "from HS256 to RS256 in Sprint 4 (commit 556beb2). Keys are stored "
                    "base64-encoded in environment variables JWT_PRIVATE_KEY_B64 and "
                    "JWT_PUBLIC_KEY_B64 and decoded at runtime in core/config.py."
                ),
            },
            {
                "title": "Role-Based Access Control — RBAC Design Patterns",
                "query": "role based access control RBAC design patterns implementation",
                "filename": "Role Based Access Control Guide.pdf",
                "source": "arxiv",
            },
            {
                "title": "Password Hashing with bcrypt — Security Analysis",
                "query": "bcrypt password hashing salting security cryptography",
                "filename": "Password Hashing Security Analysis.pdf",
                "source": "arxiv",
            },
            {
                "title": "Rate Limiting Algorithms — Token Bucket and Sliding Window",
                "query": "rate limiting algorithms API protection token bucket sliding window",
                "filename": "Rate Limiting Algorithms.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── Sprint 2 — AI and Payment Integration ────────────────────────────────
    {
        "section": "Sprint 2 — AI and Payment Integration",
        "folder":  "4. System Development/Sprint 2 - AI and Payment Integration/Sprint Execution/Research Papers",
        "papers": [
            {
                "title": "Whisper — Robust Speech Recognition via Large-Scale Weak Supervision",
                "query": "Whisper robust speech recognition large scale weak supervision OpenAI 2022",
                "filename": "Whisper Robust Speech Recognition.pdf",
                "source": "arxiv",
                "arxiv_id": "2212.04356",
            },
            {
                "title": "Whisper Fine-tuning on Nepali Language (Rijal et al., 2024)",
                "query": "Whisper fine-tuning Nepali language arXiv 2411.12587",
                "filename": "Whisper Fine-tuning Nepali Language Rijal 2024.pdf",
                "source": "arxiv",
                "arxiv_id": "2411.12587",
            },
            {
                "title": "Fine-tuning Whisper for Low-Resource Language Speech Recognition",
                "query": "fine-tuning whisper low resource language speech recognition",
                "filename": "Fine-tuning Whisper Low Resource Languages.pdf",
                "source": "arxiv",
            },
            {
                "title": "Transformer Architecture for Speech Processing",
                "query": "transformer architecture ASR speech processing attention mechanism 2023",
                "filename": "Transformer Architecture for ASR.pdf",
                "source": "arxiv",
            },
            {
                "title": "eSewa Payment Gateway — Integration Architecture",
                "query": "digital payment gateway integration mobile application Nepal",
                "filename": "Digital Payment Gateway Integration.pdf",
                "source": "summary",
                "summary_url": "https://developer.esewa.com.np",
                "abstract": (
                    "eSewa is Nepal's leading digital payment solution, providing a Flutter "
                    "SDK and a server-to-server verification API. Integration pattern used "
                    "in VoiceScribe: (1) Flutter app fetches eSewa credentials via "
                    "GET /users/esewa-config (backend never exposes the secret key to the "
                    "client); (2) Flutter esewa_flutter_sdk triggers the eSewa Webview "
                    "payment flow; (3) On success the app sends the transaction reference "
                    "to POST /users/subscription/esewa; (4) The backend performs "
                    "server-to-server verification against eSewa's V2 API endpoint at "
                    "https://rc.esewa.com.np/mobile/transaction validating the transaction "
                    "status equals COMPLETE before writing the subscription to the database. "
                    "This prevents client-side payment forgery."
                ),
            },
            {
                "title": "Subscription and Quota Management Systems",
                "query": "SaaS subscription management quota billing system design",
                "filename": "Subscription Quota Management Systems.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── Sprint 3 — AI Refinement and Security Hardening ──────────────────────
    {
        "section": "Sprint 3 — AI Refinement and Security Hardening",
        "folder":  "4. System Development/Sprint 3 - AI Refinement and Security Hardening/Sprint Execution/Research Papers",
        "papers": [
            {
                "title": "Neural Machine Transliteration — LSTM Sequence-to-Sequence Models",
                "query": "neural machine transliteration LSTM encoder decoder sequence",
                "filename": "Neural Machine Transliteration LSTM.pdf",
                "source": "arxiv",
            },
            {
                "title": "Attention Mechanism in Neural Networks — Bahdanau Attention",
                "query": "Bahdanau attention mechanism seq2seq neural machine translation 2015",
                "filename": "Bahdanau Attention Mechanism.pdf",
                "source": "arxiv",
                "arxiv_id": "1409.0473",
            },
            {
                "title": "Audio Segmentation and Chunking for ASR Systems",
                "query": "audio segmentation chunking automatic speech recognition VAD",
                "filename": "Audio Segmentation for ASR.pdf",
                "source": "arxiv",
            },
            {
                "title": "Email Verification and OTP Systems — Security Design",
                "query": "OTP one-time password email verification security design",
                "filename": "OTP Email Verification Security.pdf",
                "source": "arxiv",
            },
            {
                "title": "Input Sanitization and XSS Prevention",
                "query": "input sanitization XSS cross-site scripting prevention web security",
                "filename": "Input Sanitization XSS Prevention.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── Sprint 4 — Security Migration and Infrastructure ──────────────────────
    {
        "section": "Sprint 4 — Security Migration and Infrastructure",
        "folder":  "4. System Development/Sprint 4 - Security Migration and Infrastructure/Sprint Execution/Research Papers",
        "papers": [
            {
                "title": "Cloud Database Migration — On-Premises to AWS RDS",
                "query": "cloud database migration PostgreSQL AWS RDS best practices",
                "filename": "Cloud Database Migration AWS RDS.pdf",
                "source": "arxiv",
            },
            {
                "title": "AWS RDS PostgreSQL — Architecture and Security Configuration",
                "query": "AWS RDS PostgreSQL SSL connection pooling security configuration",
                "filename": "AWS RDS PostgreSQL Architecture.pdf",
                "source": "summary",
                "summary_url": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html",
                "abstract": (
                    "Amazon RDS for PostgreSQL provides a managed relational database service "
                    "with automated backups, software patching, and Multi-AZ deployments. "
                    "VoiceScribe uses RDS with: (1) SSL enforcement — sslmode=require in all "
                    "SQLAlchemy connection strings; (2) IPv4-only resolution — hostaddr param "
                    "set to the resolved IPv4 address preventing IPv6 fallback issues; "
                    "(3) Connection pooling — pool_size=5, max_overflow=10, pool_pre_ping=True, "
                    "pool_recycle=300 seconds; (4) Environment variable injection — credentials "
                    "stored in .env (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, "
                    "POSTGRES_PORT, POSTGRES_DB) and never hardcoded in source code. "
                    "Migration was performed via pg_dump dump-and-restore in commit 2f673ac."
                ),
            },
            {
                "title": "Cryptographic Password Reset Token Design",
                "query": "password reset token SHA256 hashing single use expiry security",
                "filename": "Password Reset Token Security Design.pdf",
                "source": "arxiv",
            },
            {
                "title": "CORS Security in REST APIs",
                "query": "cross origin resource sharing CORS security REST API configuration",
                "filename": "CORS Security REST APIs.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── Sprint 5 — Refinement and Stabilization ───────────────────────────────
    {
        "section": "Sprint 5 — Refinement and Stabilization",
        "folder":  "4. System Development/Sprint 5 - Refinement and Stabilization/Sprint Execution/Research Papers",
        "papers": [
            {
                "title": "API Integration Testing with pytest — Best Practices",
                "query": "pytest API integration testing FastAPI TestClient mocking",
                "filename": "API Integration Testing with pytest.pdf",
                "source": "arxiv",
            },
            {
                "title": "Subscription Billing — Cumulative Quota and Renewal Logic",
                "query": "SaaS billing quota renewal monthly yearly subscription design",
                "filename": "Subscription Billing Quota Design.pdf",
                "source": "summary",
                "summary_url": "https://stripe.com/docs/billing",
                "abstract": (
                    "VoiceScribe implements a non-cron cumulative quota system for yearly "
                    "subscriptions. Rather than resetting minutes_used on a schedule, the "
                    "backend computes the allowed cumulative cap dynamically: "
                    "months_elapsed = relativedelta(today, period_start).months; "
                    "total_allowed = monthly_quota * (months_elapsed + 1). "
                    "This approach means Month 1 allows 1× quota, Month 2 allows 2× quota, "
                    "automatically growing without background jobs. The usage column "
                    "(minutes_used) never resets — the window expands. This pattern avoids "
                    "cron-job infrastructure while still enforcing fair monthly throttling. "
                    "Implementation lives in backend/api/routes/transcription.py."
                ),
            },
            {
                "title": "Flutter Secure Storage and Token Management",
                "query": "flutter secure storage JWT token management mobile security",
                "filename": "Flutter Secure Storage Token Management.pdf",
                "source": "arxiv",
            },
        ],
    },

    # ── 5. Testing ────────────────────────────────────────────────────────────
    {
        "section": "5. Testing",
        "folder":  "5. Testing/Sprint Execution/Research Papers",
        "papers": [
            {
                "title": "Software Testing Methodologies — Unit, Integration, System Testing",
                "query": "software testing unit integration system test methodologies",
                "filename": "Software Testing Methodologies.pdf",
                "source": "arxiv",
            },
            {
                "title": "API Security Testing Techniques",
                "query": "API security testing penetration testing authentication fuzzing",
                "filename": "API Security Testing Techniques.pdf",
                "source": "arxiv",
            },
            {
                "title": "Machine Learning Model Evaluation — Metrics and Benchmarks",
                "query": "speech recognition ASR evaluation WER word error rate benchmark",
                "filename": "ASR Model Evaluation Metrics.pdf",
                "source": "arxiv",
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    """Strip characters that cannot be encoded in latin-1 (fpdf2 core fonts)."""
    replacements = {
        "\u2014": "-",  # em dash
        "\u2013": "-",  # en dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2022": "*",  # bullet
        "\u00e9": "e",  # e acute
        "\u00e0": "a",  # a grave
        "\u00fc": "u",  # u umlaut
    }
    for ch, rep in replacements.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class VoiceScribePDF(FPDF):
    """Dark-themed branded PDF for VoiceScribe research documents."""

    def header(self):
        from fpdf.enums import XPos, YPos
        # Dark background strip
        self.set_fill_color(*COLOUR_BG)
        self.rect(0, 0, 210, 24, "F")

        # Accent bar
        self.set_fill_color(*COLOUR_ACCENT)
        self.rect(0, 0, 4, 24, "F")

        # Title
        self.set_xy(10, 7)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*COLOUR_HEADING)
        self.cell(130, 8, "VoiceScribe FYP Research Reference",
                  new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Date stamp
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLOUR_MUTED)
        self.cell(0, 8, datetime.now().strftime("%d %b %Y"),
                  align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_fill_color(*COLOUR_BG)
        self.rect(0, self.get_y() - 2, 210, 20, "F")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLOUR_MUTED)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, text: str):
        from fpdf.enums import XPos, YPos
        self.ln(4)
        self.set_fill_color(*COLOUR_ACCENT)
        self.rect(10, self.get_y(), 3, 8, "F")
        self.set_x(16)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COLOUR_HEADING)
        self.cell(0, 8, _safe(text),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def body_text(self, text: str, size: int = 10):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*COLOUR_BODY)
        self.set_x(10)
        self.multi_cell(190, 5.5, _safe(text))
        self.ln(2)

    def metadata_row(self, label: str, value: str):
        from fpdf.enums import XPos, YPos
        self.set_x(10)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*COLOUR_MUTED)
        self.cell(38, 6, _safe(label) + ":",
                  new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*COLOUR_BODY)
        self.multi_cell(152, 6, _safe(value))

    def divider(self):
        self.set_draw_color(*COLOUR_BORDER)
        self.line(10, self.get_y() + 1, 200, self.get_y() + 1)
        self.ln(5)


def build_summary_pdf(out_path: Path, paper: dict, arxiv_result: dict | None = None):
    """Generate a dark-themed A4 summary PDF for a research reference."""
    pdf = VoiceScribePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Hero title block
    pdf.set_fill_color(*COLOUR_CARD)
    pdf.rect(0, 24, 210, 44, "F")
    from fpdf.enums import XPos, YPos
    pdf.set_y(28)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*COLOUR_HEADING)
    pdf.multi_cell(190, 8, _safe(paper["title"]))
    pdf.ln(2)

    if arxiv_result:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COLOUR_ACCENT)
        authors = ", ".join(arxiv_result.get("authors", [])[:4])
        if len(arxiv_result.get("authors", [])) > 4:
            authors += " et al."
        pdf.cell(0, 6, _safe(authors),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(72)

    # Metadata block
    pdf.section_title("Document Information")
    pdf.metadata_row("Section", paper.get("section_label", "VoiceScribe FYP"))
    pdf.metadata_row("Status", "Research Reference")
    pdf.metadata_row("Generated", datetime.now().strftime("%d %B %Y, %H:%M"))
    if arxiv_result:
        pdf.metadata_row("ArXiv ID", arxiv_result.get("id", "—"))
        pdf.metadata_row("Published", arxiv_result.get("published", "—")[:10])
        pdf.metadata_row("Source URL", arxiv_result.get("url", "—"))
    elif paper.get("summary_url"):
        pdf.metadata_row("Reference URL", paper["summary_url"])

    pdf.divider()

    # Abstract / body
    pdf.section_title("Abstract")
    abstract = ""
    if arxiv_result and arxiv_result.get("abstract"):
        abstract = arxiv_result["abstract"]
    elif paper.get("abstract"):
        abstract = paper["abstract"]
    else:
        abstract = f"Research reference for: {paper['title']}."
    pdf.body_text(abstract)

    pdf.divider()

    # Relevance to VoiceScribe
    pdf.section_title("Relevance to VoiceScribe")
    pdf.body_text(
        f"This paper is referenced in the '{paper.get('section_label', 'VoiceScribe FYP')}' "
        f"documentation section. The concepts covered support the design and implementation "
        f"decisions recorded in the corresponding sprint or system design artifact."
    )

    # Keywords from query
    pdf.divider()
    pdf.section_title("Keywords")
    pdf.body_text(paper.get("query", "").replace(" ", "  ·  "))

    pdf.output(str(out_path))


# ─────────────────────────────────────────────────────────────────────────────
# ArXiv API
# ─────────────────────────────────────────────────────────────────────────────

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def arxiv_search(query: str, max_results: int = 3) -> list[dict]:
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "max_results":  max_results,
        "sortBy":       "relevance",
        "sortOrder":    "descending",
    })
    url = f"{ARXIV_API}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = r.read()
        root = ET.fromstring(data)
        results = []
        for entry in root.findall("atom:entry", NS):
            aid_raw = (entry.findtext("atom:id", "", NS) or "").strip()
            aid = aid_raw.split("/abs/")[-1].replace("/", "_")
            results.append({
                "id":        aid,
                "title":     (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " "),
                "abstract":  (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " "),
                "published": (entry.findtext("atom:published", "", NS) or "").strip(),
                "url":       f"https://arxiv.org/abs/{aid}",
                "pdf_url":   f"https://arxiv.org/pdf/{aid}.pdf",
                "authors":   [
                    (a.findtext("atom:name", "", NS) or "").strip()
                    for a in entry.findall("atom:author", NS)
                ],
            })
        return results
    except Exception as exc:
        print(f"    [ArXiv API error] {exc}")
        return []


def arxiv_by_id(arxiv_id: str) -> dict | None:
    """Fetch a paper by its exact ArXiv ID."""
    params = urllib.parse.urlencode({
        "id_list":    arxiv_id,
        "max_results": 1,
    })
    url = f"{ARXIV_API}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = r.read()
        root  = ET.fromstring(data)
        entry = root.find("atom:entry", NS)
        if entry is None:
            return None
        aid_raw = (entry.findtext("atom:id", "", NS) or "").strip()
        aid = aid_raw.split("/abs/")[-1].replace("/", "_")
        return {
            "id":        aid,
            "title":     (entry.findtext("atom:title", "", NS) or "").strip().replace("\n", " "),
            "abstract":  (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " "),
            "published": (entry.findtext("atom:published", "", NS) or "").strip(),
            "url":       f"https://arxiv.org/abs/{aid}",
            "pdf_url":   f"https://arxiv.org/pdf/{aid}.pdf",
            "authors":   [
                (a.findtext("atom:name", "", NS) or "").strip()
                for a in entry.findall("atom:author", NS)
            ],
        }
    except Exception as exc:
        print(f"    [ArXiv ID fetch error] {exc}")
        return None


def download_pdf(url: str, dest: Path, timeout: int = 30) -> bool:
    """Stream a PDF from URL to dest; return True on success."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "VoiceScribe-FYP-Scraper/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
        # Quick sanity-check: PDFs start with %PDF
        if content[:4] != b"%PDF":
            return False
        dest.write_bytes(content)
        return True
    except Exception as exc:
        print(f"    [PDF download error] {exc}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Main scraper loop
# ─────────────────────────────────────────────────────────────────────────────

def scrape():
    print("\n" + "═" * 64)
    print("  VoiceScribe FYP — Research Scraper")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 64 + "\n")

    metadata: list[dict] = []
    total_saved   = 0
    total_skipped = 0

    for topic in RESEARCH_TOPICS:
        folder_path = BASE_DIR / topic["folder"]
        folder_path.mkdir(parents=True, exist_ok=True)

        print(f"\n{'─'*60}")
        print(f"  📂  {topic['section']}")
        print(f"{'─'*60}")

        for paper in topic["papers"]:
            out_path = folder_path / paper["filename"]
            paper["section_label"] = topic["section"]

            # Skip if already downloaded
            if out_path.exists():
                print(f"  ✓  [SKIP] {paper['filename']}")
                total_skipped += 1
                continue

            print(f"  →  {paper['filename']}")

            arxiv_result = None
            downloaded   = False

            # 1. Summary / custom-abstract papers — always generate PDF
            if paper["source"] == "summary":
                print("       generating summary PDF …")
                build_summary_pdf(out_path, paper)
                downloaded = True

            # 2. Papers with a known ArXiv ID — fetch then try PDF download
            elif paper.get("arxiv_id"):
                print(f"       fetching ArXiv:{paper['arxiv_id']} …")
                arxiv_result = arxiv_by_id(paper["arxiv_id"])
                if arxiv_result:
                    print(f"       downloading PDF …")
                    downloaded = download_pdf(arxiv_result["pdf_url"], out_path)
                    if downloaded:
                        print("       ✓ PDF saved")
                    else:
                        print("       ✗ PDF unavailable — generating summary")
                        build_summary_pdf(out_path, paper, arxiv_result)
                        downloaded = True
                time.sleep(1)

            # 3. Search ArXiv by query
            else:
                print(f"       searching ArXiv …")
                results = arxiv_search(paper["query"], max_results=3)
                if results:
                    arxiv_result = results[0]
                    print(f"       best match: {arxiv_result['title'][:60]}…")
                    print(f"       downloading PDF …")
                    downloaded = download_pdf(arxiv_result["pdf_url"], out_path)
                    if downloaded:
                        print("       ✓ PDF saved")
                    else:
                        print("       ✗ PDF unavailable — generating summary")
                        build_summary_pdf(out_path, paper, arxiv_result)
                        downloaded = True
                else:
                    print("       no ArXiv results — generating summary PDF")
                    build_summary_pdf(out_path, paper)
                    downloaded = True
                time.sleep(2)   # be polite to ArXiv

            if downloaded:
                total_saved += 1
                meta_entry = {
                    "filename":    paper["filename"],
                    "title":       paper.get("title", ""),
                    "section":     topic["section"],
                    "folder":      str(folder_path.relative_to(BASE_DIR)),
                    "source":      paper["source"],
                    "downloaded_at": datetime.now().isoformat(),
                }
                if arxiv_result:
                    meta_entry.update({
                        "arxiv_id":  arxiv_result.get("id", ""),
                        "arxiv_url": arxiv_result.get("url", ""),
                        "published": arxiv_result.get("published", "")[:10],
                        "authors":   arxiv_result.get("authors", [])[:4],
                    })
                elif paper.get("summary_url"):
                    meta_entry["reference_url"] = paper["summary_url"]

                metadata.append(meta_entry)

    # Save consolidated metadata
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if METADATA_FILE.exists():
        try:
            existing = json.loads(METADATA_FILE.read_text())
        except Exception:
            pass
    # Merge: replace entries with same filename
    existing_map = {e["filename"]: e for e in existing}
    for m in metadata:
        existing_map[m["filename"]] = m
    METADATA_FILE.write_text(json.dumps(list(existing_map.values()), indent=2))

    print("\n" + "═" * 64)
    print(f"  ✓  Scrape complete!")
    print(f"     Files saved  : {total_saved}")
    print(f"     Files skipped: {total_skipped}")
    print(f"     Metadata     : {METADATA_FILE}")
    print("═" * 64 + "\n")


if __name__ == "__main__":
    scrape()
