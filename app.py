"""
Streamlit UI for the E-commerce Support Resolution Agent.
Multi-Agent AI Demo — Purple Merit Technologies Assessment.
"""

import streamlit as st
import json
import time
import os
import sys
import io
from pathlib import Path

# Force UTF-8 encoding for Windows stability (prevents Emoji/Rocket crash)
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent))

from src.models import TicketInput, OrderContext, OrderItem, CustomerTier
from src.orchestrator import SupportOrchestrator
from src.ingestion.document_loader import DocumentLoader
from src.vectorstore.store import PolicyVectorStore
from config.settings import settings


# ────────────────────────────────────────────────
# Page Config
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Support Resolution Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────
# Premium CSS Theme
# ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Hero Header ── */
    .hero {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
        position: relative;
    }
    .hero .subtitle {
        opacity: 0.7;
        font-size: 0.95rem;
        font-weight: 400;
        position: relative;
    }
    .hero .badge-row {
        margin-top: 1rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        position: relative;
    }
    .hero .tech-badge {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.85);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        backdrop-filter: blur(4px);
    }

    /* ── Metric Cards ── */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.2rem;
        border-radius: 14px;
        text-align: center;
        border: 1px solid rgba(99,102,241,0.2);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99,102,241,0.15);
    }
    .metric-card .value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #818cf8;
        margin: 0;
        text-transform: uppercase;
    }
    .metric-card .label {
        color: rgba(255,255,255,0.5);
        font-size: 0.75rem;
        margin: 0.2rem 0 0 0;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ── Status Pills ── */
    .pill-approved {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        color: #6ee7b7;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .pill-escalated {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        color: #fca5a5;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .pill-rewrite {
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
        color: #fcd34d;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* ── Response Box ── */
    .response-card {
        background: linear-gradient(145deg, #1e1e30 0%, #1a1a2e 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 16px;
        padding: 1.5rem;
        font-size: 0.92rem;
        line-height: 1.7;
        color: rgba(255,255,255,0.85);
        margin: 0.5rem 0;
    }

    /* ── Citation Badge ── */
    .cite-badge {
        display: inline-block;
        background: rgba(99,102,241,0.15);
        color: #a5b4fc;
        padding: 3px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        margin: 3px 4px 3px 0;
        border: 1px solid rgba(99,102,241,0.25);
        font-weight: 500;
    }

    /* ── Pipeline Step ── */
    .pipeline-step {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid;
        font-size: 0.88rem;
    }
    .step-1 { background: rgba(251,191,36,0.08); border-color: #f59e0b; color: #fbbf24; }
    .step-2 { background: rgba(59,130,246,0.08); border-color: #3b82f6; color: #60a5fa; }
    .step-3 { background: rgba(16,185,129,0.08); border-color: #10b981; color: #34d399; }
    .step-4 { background: rgba(239,68,68,0.08); border-color: #ef4444; color: #f87171; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: rgba(255,255,255,0.9);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: rgba(255,255,255,0.65);
        font-size: 0.88rem;
    }

    /* ── Action Row ── */
    .action-item {
        background: rgba(99,102,241,0.08);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 10px;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.88rem;
        color: rgba(255,255,255,0.8);
    }
</style>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────────
# Session State
# ────────────────────────────────────────────────
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "results_history" not in st.session_state:
    st.session_state.results_history = []
if "init_error" not in st.session_state:
    st.session_state.init_error = None


# ────────────────────────────────────────────────
# System Initialization (auto on first load)
# ────────────────────────────────────────────────
def initialize_system():
    """Initialize the vector store and orchestrator from .env config."""
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


# Auto-initialize on first load
if not st.session_state.initialized and st.session_state.init_error is None:
    with st.spinner("Initializing AI agents and vector store..."):
        initialize_system()


# ────────────────────────────────────────────────
# Hero Header
# ────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>E-commerce Support Resolution Agent</h1>
    <div class="subtitle">Multi-Agent AI System &mdash; CrewAI + RAG Pipeline with Compliance Loop</div>
    <div class="badge-row">
        <span class="tech-badge">CrewAI</span>
        <span class="tech-badge">LangChain</span>
        <span class="tech-badge">FAISS</span>
        <span class="tech-badge">Google Gemini 3.1 Flash Lite ⚡</span>
        <span class="tech-badge">HuggingFace Embeddings</span>
        <span class="tech-badge">4 AI Agents</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## System Info")

    if st.session_state.initialized:
        st.success("System Ready")
    elif st.session_state.init_error:
        st.error(f"Init Error: {st.session_state.init_error}")
        if st.button("Retry Initialization", type="primary"):
            initialize_system()
            st.rerun()
    else:
        st.warning("Initializing...")

    st.markdown("---")

    # Read-only config display
    model_name = settings.LLM_MODEL.split("/")[-1] if "/" in settings.LLM_MODEL else settings.LLM_MODEL
    provider = settings.LLM_MODEL.split("/")[0] if "/" in settings.LLM_MODEL else "unknown"

    st.markdown("### Configuration")
    st.markdown(f"""
    - **Provider:** `{provider}`
    - **Model:** `{model_name}`
    - **Embeddings:** `all-MiniLM-L6-v2`
    - **Vector Store:** FAISS
    - **Policy Docs:** 13
    - **Retriever K:** {settings.RETRIEVER_K}
    """)

    st.markdown("---")
    st.markdown("### Agent Pipeline")
    st.markdown("""
<div class="pipeline-step step-1"><strong>1. Triage Agent</strong> &mdash; Classify &amp; prioritize</div>
<div class="pipeline-step step-2"><strong>2. Retriever Agent</strong> &mdash; Search policies (FAISS)</div>
<div class="pipeline-step step-3"><strong>3. Resolution Writer</strong> &mdash; Draft response</div>
<div class="pipeline-step step-4"><strong>4. Compliance Agent</strong> &mdash; Safety audit</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Session Stats")
    total = len(st.session_state.results_history)
    approved = sum(1 for r in st.session_state.results_history if r.get("compliance_status") == "approved")
    cited = sum(1 for r in st.session_state.results_history if r.get("citations"))
    st.metric("Tickets Processed", total)
    st.metric("Approval Rate", f"{(approved/total*100):.0f}%" if total > 0 else "N/A")
    st.metric("Citation Rate", f"{(cited/total*100):.0f}%" if total > 0 else "N/A")


# ────────────────────────────────────────────────
# Main Content — Tabs
# ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["New Ticket", "Sample Tickets", "Results History"])


# ═══════════════════════════════════════════
# TAB 1 — New Ticket
# ═══════════════════════════════════════════
with tab1:
    st.markdown("### Submit a Support Ticket")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name", value="John Doe", key="t1_name")
        customer_email = st.text_input("Customer Email", value="john@email.com", key="t1_email")
        customer_tier = st.selectbox("Loyalty Tier", ["bronze", "silver", "gold", "platinum"], key="t1_tier")

    with col2:
        ticket_id = st.text_input("Ticket ID", value=f"TKT-{int(time.time())%10000:04d}", key="t1_id")
        has_order = st.checkbox("Include Order Context", value=True, key="t1_order")

    ticket_text = st.text_area(
        "Customer Message",
        height=130,
        placeholder="Describe the customer's issue...",
        value="I received my order yesterday but one of the items is damaged. The package was clearly mishandled during shipping. I'd like a full refund for the damaged item.",
        key="t1_text",
    )

    if has_order:
        st.markdown("#### Order Details")
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            order_id = st.text_input("Order ID", value="ORD-2026-99001", key="t1_oid")
            order_date = st.text_input("Order Date", value="2026-03-25", key="t1_odate")
        with oc2:
            delivery_date = st.text_input("Delivery Date", value="2026-03-27", key="t1_ddate")
            total_amount = st.number_input("Order Total ($)", value=149.99, key="t1_total")
        with oc3:
            payment = st.selectbox("Payment Method", ["credit_card", "paypal", "wallet", "affirm"], key="t1_pay")
            shipping = st.selectbox("Shipping Method", ["standard", "expedited", "overnight"], key="t1_ship")

        item_name = st.text_input("Item Name", value="Wireless Bluetooth Speaker", key="t1_item")
        item_price = st.number_input("Item Price ($)", value=149.99, key="t1_price")

    if st.button("Process Ticket", type="primary", use_container_width=True, key="t1_submit"):
        if not st.session_state.initialized:
            st.error("System not initialized. Check .env configuration and restart.")
        else:
            # Build ticket
            order_ctx = None
            if has_order:
                order_ctx = OrderContext(
                    order_id=order_id,
                    order_date=order_date,
                    delivery_date=delivery_date if delivery_date else None,
                    items=[OrderItem(name=item_name, price=item_price, category="general")],
                    total_amount=total_amount,
                    payment_method=payment,
                    shipping_method=shipping,
                    shipping_address_country="US",
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

            # Process
            with st.spinner("Running 4-agent pipeline..."):
                start = time.time()
                try:
                    result = st.session_state.orchestrator.resolve_ticket(ticket)
                    elapsed = time.time() - start

                    result_dict = {
                        "ticket_id": result.ticket_id,
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

                    # ── Display Results ──
                    st.markdown("---")
                    st.markdown("### Resolution Result")

                    # Metrics row
                    st.markdown(f"""
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="value">{result.issue_type}</div>
                            <div class="label">Issue Type</div>
                        </div>
                        <div class="metric-card">
                            <div class="value">{result.priority}</div>
                            <div class="label">Priority</div>
                        </div>
                        <div class="metric-card">
                            <div class="value">
                                <span class="pill-{'approved' if result.compliance_status == 'approved' else 'escalated'}">{result.compliance_status}</span>
                            </div>
                            <div class="label">Compliance</div>
                        </div>
                        <div class="metric-card">
                            <div class="value">{elapsed:.1f}s</div>
                            <div class="label">Processing Time</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Customer Response
                    st.markdown("#### Customer Response")
                    st.markdown(f'<div class="response-card">{result.customer_response}</div>', unsafe_allow_html=True)

                    # Citations
                    if result.citations:
                        st.markdown("#### Policy Citations")
                        badges = "".join(f'<span class="cite-badge">{c}</span>' for c in result.citations)
                        st.markdown(badges, unsafe_allow_html=True)

                    # Actions
                    if result.actions_to_take:
                        st.markdown("#### Critical Actions")
                        for action in result.actions_to_take:
                            st.markdown(f'<div class="action-item">✔️ {action}</div>', unsafe_allow_html=True)

                    # Internal Notes
                    with st.expander("Internal Notes (not visible to customer)"):
                        st.text(result.internal_notes)

                    if result.requires_escalation:
                        st.warning(f"**Escalation Required:** {result.escalation_reason}")

                    if result.rewrite_count > 0:
                        st.info(f"Response was rewritten {result.rewrite_count} time(s) by the compliance agent.")

                except Exception as e:
                    st.error(f"Error processing ticket: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())


# ═══════════════════════════════════════════
# TAB 2 — Sample Tickets
# ═══════════════════════════════════════════
with tab2:
    st.markdown("### Pre-Built Test Tickets")
    st.markdown("These 23 tickets cover standard, exception-heavy, conflict, not-in-policy, and mandatory escalation scenarios.")

    samples_path = os.path.join(os.path.dirname(__file__), "tests", "test_tickets.json")
    if os.path.exists(samples_path):
        with open(samples_path, "r", encoding="utf-8") as f:
            samples = json.load(f)

        for sample in samples:
            tier_emoji = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}.get(sample.get("customer_tier", ""), "")
            with st.expander(f"{tier_emoji} {sample['ticket_id']} — {sample['customer_name']} ({sample.get('customer_tier', 'N/A')})"):
                st.markdown(f"**Message:** {sample['ticket_text']}")
                if sample.get("order_context"):
                    st.json(sample["order_context"])
    else:
        st.info("No sample tickets found. Add `test_tickets.json` to the `tests/` directory.")


# ═══════════════════════════════════════════
# TAB 3 — Results History
# ═══════════════════════════════════════════
with tab3:
    st.markdown("### Results History")

    if st.session_state.results_history:
        for i, result in enumerate(reversed(st.session_state.results_history)):
            status = result["compliance_status"]
            pill_class = "pill-approved" if status == "approved" else "pill-escalated"
            with st.expander(f"{result['ticket_id']} — {status} — {result['time']}s"):
                st.markdown(f"**Issue:** {result['issue_type']} | **Priority:** {result['priority']}")
                st.markdown(f'<span class="{pill_class}">{status}</span>', unsafe_allow_html=True)
                st.markdown(f"**Response:**\n\n{result['customer_response']}")
                if result["citations"]:
                    badges = "".join(f'<span class="cite-badge">{c}</span>' for c in result["citations"])
                    st.markdown(f"**Citations:** {badges}", unsafe_allow_html=True)
    else:
        st.info("No tickets processed yet. Submit a ticket in the 'New Ticket' tab.")
