"""
Streamlit UI — ResolveAI
4-Agent AI Support Pipeline | Gemini 3.1 Flash Lite ⚡
UPI · Credit Card · Cash on Delivery
"""

import streamlit as st
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# ── Force UTF-8 for Windows stability ──
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent))

from src.models import TicketInput, OrderContext, OrderItem
from src.orchestrator import SupportOrchestrator
from src.ingestion.document_loader import DocumentLoader
from src.vectorstore.store import PolicyVectorStore
from src.email_sender import send_resolution_email
from config.settings import settings

# ════════════════════════════════════════════════════
# Page Config
# ════════════════════════════════════════════════════
st.set_page_config(
    page_title="ResolveAI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════
# Premium CSS — Glassmorphism Dark Mode
# ════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #070B14;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d111e; }
::-webkit-scrollbar-thumb { background: #2d3561; border-radius: 3px; }

/* ── Hero ── */
.hero-wrap {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 20px;
    padding: 2.8rem 2.4rem 2.2rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 1.6rem;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(139,92,246,0.18) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-wrap::after {
    content: '';
    position: absolute;
    bottom: -40px; left: -40px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-eyebrow {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #a78bfa;
    margin: 0 0 10px 0;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 900;
    color: #ffffff;
    margin: 0 0 6px 0;
    letter-spacing: -1px;
    line-height: 1.1;
    position: relative;
}
.hero-sub {
    font-size: 0.92rem;
    color: rgba(255,255,255,0.45);
    margin: 0 0 1.4rem 0;
    position: relative;
}
.badge-row { display: flex; gap: 8px; flex-wrap: wrap; position: relative; }
.badge {
    background: rgba(139,92,246,0.12);
    border: 1px solid rgba(139,92,246,0.25);
    color: #c4b5fd;
    padding: 4px 13px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.3px;
    transition: all 0.2s;
}
.badge:hover {
    background: rgba(139,92,246,0.22);
    border-color: rgba(139,92,246,0.5);
    color: #fff;
}
.badge-cyan {
    background: rgba(6,182,212,0.12);
    border-color: rgba(6,182,212,0.25);
    color: #67e8f9;
}

/* ── Stat Cards (top row) ── */
.stat-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 1.2rem 0; }
.stat-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.1rem 1rem;
    text-align: center;
    transition: transform 0.25s, box-shadow 0.25s, border-color 0.25s;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(139,92,246,0.04) 0%, transparent 60%);
    border-radius: 14px;
}
.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(139,92,246,0.12);
    border-color: rgba(139,92,246,0.2);
}
.stat-val {
    font-size: 1.35rem;
    font-weight: 800;
    color: #a78bfa;
    margin: 0;
    position: relative;
}
.stat-val.green { color: #34d399; }
.stat-val.cyan  { color: #22d3ee; }
.stat-val.amber { color: #fbbf24; }
.stat-lbl {
    font-size: 0.68rem;
    color: rgba(255,255,255,0.35);
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 4px 0 0 0;
    position: relative;
}

/* ── Status pills ── */
.pill {
    display: inline-block;
    padding: 3px 13px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.5px;
}
.pill-approved { background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3); color: #34d399; }
.pill-escalated { background: rgba(248,113,113,0.12); border: 1px solid rgba(248,113,113,0.3); color: #f87171; }
.pill-rewrite { background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; }

/* ── Glass Panel (response / sections) ── */
.glass-panel {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin: 0.6rem 0;
    line-height: 1.75;
    color: rgba(255,255,255,0.82);
    font-size: 0.93rem;
}
.glass-panel-accent {
    border-left: 3px solid #a78bfa;
    background: rgba(139,92,246,0.06);
}

/* ── Section title ── */
.section-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.3);
    margin: 1.4rem 0 0.5rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* ── Citation badges ── */
.cite-badge {
    display: inline-block;
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.25);
    color: #a5b4fc;
    padding: 3px 11px;
    border-radius: 8px;
    font-size: 0.75rem;
    margin: 3px 4px 3px 0;
    font-weight: 500;
    transition: background 0.2s;
}
.cite-badge:hover { background: rgba(99,102,241,0.2); }

/* ── Action items ── */
.action-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    background: rgba(52,211,153,0.05);
    border: 1px solid rgba(52,211,153,0.12);
    border-radius: 10px;
    padding: 0.55rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.87rem;
    color: rgba(255,255,255,0.75);
}
.action-icon { color: #34d399; font-size: 1rem; flex-shrink: 0; margin-top: 1px; }

/* ── Pipeline steps (sidebar) ── */
.pipe-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.6rem 0.8rem;
    border-radius: 10px;
    margin: 4px 0;
    font-size: 0.82rem;
    border: 1px solid transparent;
    transition: all 0.2s;
}
.pipe-1 { background: rgba(251,191,36,0.07); border-color: rgba(251,191,36,0.15); color: #fcd34d; }
.pipe-2 { background: rgba(59,130,246,0.07); border-color: rgba(59,130,246,0.15); color: #60a5fa; }
.pipe-3 { background: rgba(52,211,153,0.07); border-color: rgba(52,211,153,0.15); color: #34d399; }
.pipe-4 { background: rgba(239,68,68,0.07); border-color: rgba(239,68,68,0.15); color: #f87171; }
.pipe-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-1 { background: #fbbf24; box-shadow: 0 0 6px #fbbf24; }
.dot-2 { background: #3b82f6; box-shadow: 0 0 6px #3b82f6; }
.dot-3 { background: #10b981; box-shadow: 0 0 6px #10b981; }
.dot-4 { background: #ef4444; box-shadow: 0 0 6px #ef4444; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #08090f 0%, #0d111e 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] .stMarkdown h4 {
    color: rgba(255,255,255,0.85);
    font-size: 0.78rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 700;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: rgba(255,255,255,0.5);
    font-size: 0.83rem;
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: rgba(255,255,255,0.85) !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(139,92,246,0.5) !important;
    box-shadow: 0 0 0 2px rgba(139,92,246,0.1) !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px !important;
    transition: all 0.25s !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px rgba(124,58,237,0.45) !important;
}

/* ── Secondary button (Email) ── */
.stButton > button:not([kind="primary"]) {
    background: rgba(6,182,212,0.1) !important;
    border: 1px solid rgba(6,182,212,0.25) !important;
    border-radius: 10px !important;
    color: #22d3ee !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: rgba(6,182,212,0.18) !important;
    border-color: rgba(6,182,212,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: rgba(255,255,255,0.45) !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(139,92,246,0.15) !important;
    color: #c4b5fd !important;
    font-weight: 700 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.02) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    color: rgba(255,255,255,0.65) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    font-size: 0.87rem !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] label {
    color: rgba(255,255,255,0.4) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #a78bfa !important;
    font-weight: 800 !important;
}

/* ── Currency toggle label ── */
.currency-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.3);
    margin-bottom: 4px;
}

/* ── divider ── */
hr { border-color: rgba(255,255,255,0.05) !important; margin: 1.2rem 0 !important; }

/* ── Alert / warning ── */
.stAlert { border-radius: 12px !important; font-size: 0.87rem !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════
USD_TO_INR = 84.0
PAYMENT_METHODS = ["UPI", "Credit / Debit Card", "Cash on Delivery"]
PAYMENT_METHOD_MAP = {
    "UPI": "upi",
    "Credit / Debit Card": "credit_card",
    "Cash on Delivery": "cash_on_delivery",
}


# ════════════════════════════════════════════════════
# Session State
# ════════════════════════════════════════════════════
for key, default in [
    ("orchestrator", None),
    ("initialized", False),
    ("results_history", []),
    ("init_error", None),
    ("currency", "INR"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ════════════════════════════════════════════════════
# System Initialization
# ════════════════════════════════════════════════════
def initialize_system():
    try:
        loader = DocumentLoader(
            policies_dir=settings.POLICIES_DIR,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        chunks = loader.load_and_chunk()
        store = PolicyVectorStore(
            embedding_model=settings.EMBEDDING_MODEL,
            store_path=settings.VECTOR_STORE_PATH,
        )
        try:
            store.load()
        except FileNotFoundError:
            store.build_index(chunks)
            store.save()

        st.session_state.orchestrator = SupportOrchestrator(
            google_api_key=settings.GOOGLE_API_KEY,
            groq_api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            vector_store=store,
        )
        st.session_state.initialized = True
        st.session_state.init_error = None
    except Exception as e:
        st.session_state.init_error = str(e)
        st.session_state.initialized = False


if not st.session_state.initialized and st.session_state.init_error is None:
    with st.spinner("Initializing AI agents and knowledge base…"):
        initialize_system()


# ════════════════════════════════════════════════════
# Hero Header
# ════════════════════════════════════════════════════
st.markdown("""
<div class="hero-wrap">
    <p class="hero-eyebrow">⚡ Powered by Gemini 3.1 Flash Lite</p>
    <h1 class="hero-title">ResolveAI</h1>
    <p class="hero-sub">4-Agent RAG Pipeline &nbsp;·&nbsp; Compliance Loop &nbsp;·&nbsp; Zero-Hallucination Guardrails</p>
    <div class="badge-row">
        <span class="badge">CrewAI</span>
        <span class="badge">LangChain</span>
        <span class="badge">FAISS</span>
        <span class="badge badge-cyan">Gemini 3.1 Flash Lite ⚡</span>
        <span class="badge">HuggingFace Embeddings</span>
        <span class="badge">Multi-Payment Support</span>
        <span class="badge">4 AI Agents</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════
with st.sidebar:
    # Status
    st.markdown("#### 🟢 System Status")
    if st.session_state.initialized:
        st.success("All agents online · Ready")
    elif st.session_state.init_error:
        st.error(f"Init failed: {st.session_state.init_error}")
        if st.button("⟳ Retry", type="primary"):
            initialize_system()
            st.rerun()
    else:
        st.warning("Initializing…")

    st.divider()

    # Currency toggle
    st.markdown('<p class="currency-label">Currency</p>', unsafe_allow_html=True)
    cur = st.radio(
        "Currency",
        ["₹ INR", "$ USD"],
        index=0 if st.session_state.currency == "INR" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="cur_toggle",
    )
    st.session_state.currency = "INR" if "INR" in cur else "USD"

    st.divider()

    # Config
    model_name = settings.LLM_MODEL.split("/")[-1] if "/" in settings.LLM_MODEL else settings.LLM_MODEL
    provider = settings.LLM_MODEL.split("/")[0] if "/" in settings.LLM_MODEL else "unknown"
    st.markdown("#### ⚙️ Configuration")
    st.markdown(f"""
- **Provider:** `{provider}`
- **Model:** `{model_name}`
- **Embeddings:** `all-MiniLM-L6-v2`
- **Vector Store:** FAISS
- **Policy Docs:** 13
- **Retriever K:** {settings.RETRIEVER_K}
    """)

    st.divider()

    # Pipeline
    st.markdown("#### 🔗 Agent Pipeline")
    st.markdown("""
<div class="pipe-step pipe-1"><span class="pipe-dot dot-1"></span><strong>Triage Agent</strong> &mdash; Classify &amp; prioritize</div>
<div class="pipe-step pipe-2"><span class="pipe-dot dot-2"></span><strong>Retriever Agent</strong> &mdash; Search policies (FAISS)</div>
<div class="pipe-step pipe-3"><span class="pipe-dot dot-3"></span><strong>Resolution Writer</strong> &mdash; Draft response</div>
<div class="pipe-step pipe-4"><span class="pipe-dot dot-4"></span><strong>Compliance Guard</strong> &mdash; Safety audit</div>
    """, unsafe_allow_html=True)

    st.divider()

    # Session stats
    total = len(st.session_state.results_history)
    approved = sum(1 for r in st.session_state.results_history if r.get("compliance_status") == "approved")
    cited = sum(1 for r in st.session_state.results_history if r.get("citations"))

    st.markdown("#### 📊 Session Stats")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Processed", total)
        st.metric("Cited", f"{(cited/total*100):.0f}%" if total else "N/A")
    with c2:
        st.metric("Approved", f"{(approved/total*100):.0f}%" if total else "N/A")
        st.metric("Errors", total - approved if total else 0)


# ════════════════════════════════════════════════════
# Helper
# ════════════════════════════════════════════════════
USE_INR = st.session_state.currency == "INR"
SYMBOL = "₹" if USE_INR else "$"


def to_display(usd_val: float) -> float:
    return round(usd_val * USD_TO_INR, 2) if USE_INR else usd_val


def from_display(display_val: float) -> float:
    return round(display_val / USD_TO_INR, 4) if USE_INR else display_val


def clean_field(raw, default="—"):
    """Extract a single clean value from raw multi-line agent output."""
    if not raw:
        return default
    # Take only the first line
    first = str(raw).strip().split("\n")[0].strip()
    # Strip label prefixes like "ISSUE_TYPE: refund"
    for prefix in ["ISSUE_TYPE:", "PRIORITY:", "STATUS:", "TYPE:", "CATEGORY:"]:
        if first.upper().startswith(prefix):
            first = first[len(prefix):].strip()
    # Take the first token only (handles "refund SUB_CATEGORY: ...")
    first = first.split()[0] if first else default
    return first.replace("_", " ").title()


def display_result(result, elapsed: float):
    """Render a clean, spacious result panel."""

    issue    = clean_field(result.issue_type)
    priority = clean_field(result.priority)
    status   = (result.compliance_status or "unknown").strip()
    rewrites = result.rewrite_count or 0

    # ── Four clean metric columns ──
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🏷️ Issue Type", issue)
    with m2:
        pri_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "🔵")
        st.metric(f"{pri_icon} Priority", priority)
    with m3:
        status_icon = "✅" if status == "approved" else "⚠️"
        st.metric(f"{status_icon} Compliance", status.capitalize())
    with m4:
        st.metric("⏱️ Processing", f"{elapsed:.1f}s")

    # ── Banners ──
    if result.requires_escalation:
        st.error(f"⚠️ **Escalation Required:** {result.escalation_reason}")
    if rewrites > 0:
        st.info(f"🔄 Response rewritten {rewrites} time(s) by the Compliance Guard.")

    # ── Customer Response ──
    st.markdown('<p class="section-title">Customer Response</p>', unsafe_allow_html=True)
    response_html = (result.customer_response or "").replace("\n", "<br>")
    st.markdown(f'<div class="glass-panel glass-panel-accent">{response_html}</div>', unsafe_allow_html=True)

    # ── Citations ──
    if result.citations:
        st.markdown('<p class="section-title">Policy Citations</p>', unsafe_allow_html=True)
        badges = "".join(f'<span class="cite-badge">📎 {c}</span>' for c in result.citations)
        st.markdown(f'<div style="margin:0.4rem 0">{badges}</div>', unsafe_allow_html=True)

    # ── Critical Actions ──
    if result.actions_to_take:
        st.markdown('<p class="section-title">Critical Actions</p>', unsafe_allow_html=True)
        for action in result.actions_to_take:
            st.markdown(
                f'<div class="action-item"><span class="action-icon">✓</span>{action}</div>',
                unsafe_allow_html=True,
            )

    # ── Internal Notes ──
    with st.expander("🔒 Internal Notes (agent-only)"):
        st.code(result.internal_notes or "No internal notes.", language=None)




# ════════════════════════════════════════════════════
# Tabs
# ════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🎫  New Ticket", "📋  Sample Tickets", "📈  Results History"])


# ═══════════════════════════════════════════════
# TAB 1 — New Ticket
# ═══════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-title">Customer Information</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name", value="Arjun Sharma", key="t1_name")
        customer_email = st.text_input("Customer Email", value="arjun.sharma@gmail.com", key="t1_email")

    with col2:
        ticket_id = st.text_input("Ticket ID", value=f"TKT-{int(time.time())%10000:04d}", key="t1_id")
        customer_tier = st.selectbox(
            "Loyalty Tier",
            ["bronze", "silver", "gold", "platinum"],
            index=1,
            key="t1_tier",
        )

    st.markdown('<p class="section-title">Issue Description</p>', unsafe_allow_html=True)
    ticket_text = st.text_area(
        "Customer Message",
        height=110,
        placeholder="Describe the customer's issue…",
        value="Mera order kal aaya lekin item damaged thi. Package bhi dented tha, shipping mein damage laga. Mujhe full refund chahiye.",
        key="t1_text",
    )

    has_order = st.checkbox("Include Order Context", value=True, key="t1_order")

    if has_order:
        st.markdown('<p class="section-title">Order Details</p>', unsafe_allow_html=True)
        oc1, oc2, oc3 = st.columns(3)

        with oc1:
            order_id = st.text_input("Order ID", value="ORD-2026-99001", key="t1_oid")
            order_date = st.text_input("Order Date", value="2026-03-25", key="t1_odate")
        with oc2:
            delivery_date = st.text_input("Delivery Date", value="2026-03-27", key="t1_ddate")
            default_total = 12599.00 if USE_INR else 149.99
            total_display = st.number_input(
                f"Order Total ({SYMBOL})",
                value=default_total,
                min_value=0.0,
                step=100.0 if USE_INR else 1.0,
                key="t1_total",
            )
        with oc3:
            payment_label = st.selectbox("Payment Method", PAYMENT_METHODS, key="t1_pay")
            payment = PAYMENT_METHOD_MAP[payment_label]
            shipping = st.selectbox("Shipping Method", ["standard", "expedited", "overnight"], key="t1_ship")

        item_name = st.text_input("Item Name", value="Wireless Bluetooth Speaker", key="t1_item")
        default_price = 12599.00 if USE_INR else 149.99
        item_price_display = st.number_input(
            f"Item Price ({SYMBOL})",
            value=default_price,
            min_value=0.0,
            step=100.0 if USE_INR else 1.0,
            key="t1_price",
        )

    # ── Submit ──
    st.markdown("")
    submitted = st.button("⚡ Process Ticket", type="primary", use_container_width=True, key="t1_submit")

    if submitted:
        if not st.session_state.initialized:
            st.error("System not initialized. Check your .env configuration and restart.")
        else:
            order_ctx = None
            if has_order:
                total_usd = from_display(total_display)
                price_usd = from_display(item_price_display)
                order_ctx = OrderContext(
                    order_id=order_id,
                    order_date=order_date,
                    delivery_date=delivery_date or None,
                    items=[OrderItem(name=item_name, price=price_usd, category="general")],
                    total_amount=total_usd,
                    payment_method=payment,
                    shipping_method=shipping,
                    shipping_address_country="IN",
                    seller_type="direct",
                )

            ticket = TicketInput(
                ticket_id=ticket_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_tier=customer_tier,
                ticket_text=ticket_text,
                order_context=order_ctx,
            )

            with st.spinner("Running 4-agent pipeline… this may take ~30s"):
                start = time.time()
                try:
                    result = st.session_state.orchestrator.resolve_ticket(ticket)
                    elapsed = time.time() - start

                    result_dict = {
                        "ticket_id": result.ticket_id,
                        "customer_name": customer_name,
                        "customer_email": customer_email,
                        "issue_type": result.issue_type,
                        "priority": result.priority,
                        "customer_response": result.customer_response,
                        "internal_notes": result.internal_notes,
                        "actions_to_take": result.actions_to_take,
                        "citations": result.citations,
                        "compliance_status": result.compliance_status,
                        "requires_escalation": result.requires_escalation,
                        "escalation_reason": result.escalation_reason,
                        "rewrite_count": result.rewrite_count,
                        "time": round(elapsed, 2),
                    }
                    st.session_state.results_history.append(result_dict)

                    st.divider()
                    st.markdown("### ✅ Resolution Complete")
                    display_result(result, elapsed)

                    # ── Email dispatch ──
                    st.divider()
                    st.markdown('<p class="section-title">Send Email to Customer</p>', unsafe_allow_html=True)
                    col_email, col_status = st.columns([2, 3])
                    with col_email:
                        send_btn = st.button("📧 Send Resolution Email", key="send_email_btn")
                    if send_btn:
                        support_email = os.getenv("SUPPORT_EMAIL", "")
                        support_pass = os.getenv("SUPPORT_EMAIL_PASSWORD", "")
                        with st.spinner("Sending email…"):
                            email_result = send_resolution_email(
                                to_email=customer_email,
                                customer_name=customer_name.split()[0],
                                ticket_id=ticket_id,
                                response_text=result.customer_response or "",
                                citations=result.citations,
                                support_email=support_email,
                                support_password=support_pass,
                            )
                        if email_result["success"]:
                            st.success(f"✅ {email_result['message']}")
                        else:
                            st.error(f"❌ {email_result['message']}")

                except Exception as e:
                    st.error(f"Error processing ticket: {str(e)}")
                    import traceback
                    with st.expander("Full traceback"):
                        st.code(traceback.format_exc())


# ═══════════════════════════════════════════════
# TAB 2 — Sample Tickets
# ═══════════════════════════════════════════════
with tab2:
    st.markdown("### 📋 Pre-Built Test Tickets")
    st.caption("23 pre-built tickets covering standard, exception, conflict, escalation, and edge-case scenarios.")

    samples_path = os.path.join(os.path.dirname(__file__), "tests", "test_tickets.json")
    if os.path.exists(samples_path):
        with open(samples_path, "r", encoding="utf-8") as f:
            samples = json.load(f)

        tier_meta = {
            "bronze": ("🥉", "#cd7f32"),
            "silver": ("🥈", "#c0c0c0"),
            "gold": ("🥇", "#ffd700"),
            "platinum": ("💎", "#e0e0ff"),
        }
        for sample in samples:
            tier = sample.get("customer_tier", "bronze")
            emoji, color = tier_meta.get(tier, ("", "#888"))
            label = f"{emoji} {sample['ticket_id']} — **{sample['customer_name']}** · {tier.capitalize()}"
            with st.expander(label):
                st.markdown(f"**Issue:**\n\n> {sample['ticket_text']}")
                if sample.get("order_context") and sample["order_context"]:
                    ctx = sample["order_context"]
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Order ID:** `{ctx.get('order_id','—')}`")
                        price_raw = ctx.get("total_amount", 0)
                        price_disp = price_raw if USE_INR else round(price_raw / USD_TO_INR, 2)
                        st.markdown(f"**Total:** {SYMBOL}{price_disp:,.2f}")
                        st.markdown(f"**Payment:** `{ctx.get('payment_method','—')}`")
                    with col_b:
                        st.markdown(f"**Shipping:** `{ctx.get('shipping_method','—')}`")
                        st.markdown(f"**State:** {ctx.get('shipping_address_state','—')}")
                        st.markdown(f"**Seller:** `{ctx.get('seller_type','—')}`")
    else:
        st.info("No sample tickets found. Add `test_tickets.json` to the `tests/` directory.")


# ═══════════════════════════════════════════════
# TAB 3 — Results History
# ═══════════════════════════════════════════════
with tab3:
    st.markdown("### 📈 Results History")

    if not st.session_state.results_history:
        st.markdown("""
        <div class="glass-panel" style="text-align:center; padding: 2.5rem; color: rgba(255,255,255,0.3);">
            <div style="font-size:2rem; margin-bottom:0.5rem;">📭</div>
            <div style="font-weight:600;">No tickets processed yet</div>
            <div style="font-size:0.82rem; margin-top:4px;">Submit a ticket in the New Ticket tab to see results here.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for result in reversed(st.session_state.results_history):
            status  = (result.get("compliance_status") or "unknown").strip()
            issue   = clean_field(result.get("issue_type"))
            priority = clean_field(result.get("priority"))
            pill    = "pill-approved" if status == "approved" else "pill-escalated"
            pri_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "🔵")

            with st.expander(
                f"**{result['ticket_id']}** — {result.get('customer_name', '—')} — {result['time']}s"
            ):
                # ── 4-column metric row ──
                h1, h2, h3, h4 = st.columns(4)
                with h1:
                    st.metric("🏷️ Issue", issue)
                with h2:
                    st.metric(f"{pri_icon} Priority", priority)
                with h3:
                    status_icon = "✅" if status == "approved" else "⚠️"
                    st.metric(f"{status_icon} Compliance", status.capitalize())
                with h4:
                    st.metric("⏱️ Time", f"{result['time']}s")

                # ── Email ──
                st.caption(f"📧 {result.get('customer_email', '—')}")

                # ── Response ──
                st.markdown('<p class="section-title">Customer Response</p>', unsafe_allow_html=True)
                resp_html = (result.get("customer_response") or "").replace("\n", "<br>")
                st.markdown(
                    f'<div class="glass-panel glass-panel-accent">{resp_html}</div>',
                    unsafe_allow_html=True,
                )

                # ── Citations ──
                if result.get("citations"):
                    st.markdown('<p class="section-title">Policy Citations</p>', unsafe_allow_html=True)
                    badges = "".join(
                        f'<span class="cite-badge">📎 {c}</span>' for c in result["citations"]
                    )
                    st.markdown(f'<div style="margin:0.3rem 0">{badges}</div>', unsafe_allow_html=True)

                # ── Escalation ──
                if result.get("requires_escalation"):
                    st.error(f"⚠️ **Escalated:** {result.get('escalation_reason', '')}")

        st.divider()
        if st.button("🗑️ Clear History", key="clear_hist"):
            st.session_state.results_history = []
            st.rerun()

