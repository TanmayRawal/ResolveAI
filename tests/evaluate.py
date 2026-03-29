"""
Evaluation suite for ResolveAI.
Runs test tickets through the pipeline and computes metrics.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Force Windows console to use UTF-8 to prevent CrewAI emoji crashes
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import TicketInput, OrderContext, OrderItem
from src.orchestrator import SupportOrchestrator
from src.ingestion.document_loader import DocumentLoader
from src.vectorstore.store import PolicyVectorStore
from config.settings import settings

# Rate limit delay between tickets (seconds) to avoid Groq TPM limits
INTER_TICKET_DELAY = 8


def load_test_tickets(filepath: str) -> list[TicketInput]:
    """Load test tickets from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    tickets = []
    for entry in raw:
        order_ctx = None
        if entry.get("order_context"):
            oc = entry["order_context"]
            items = [OrderItem(**item) for item in oc.get("items", [])]
            order_ctx = OrderContext(
                order_id=oc["order_id"],
                order_date=oc["order_date"],
                delivery_date=oc.get("delivery_date"),
                estimated_delivery=oc.get("estimated_delivery"),
                items=items,
                total_amount=oc["total_amount"],
                payment_method=oc.get("payment_method", "credit_card"),
                shipping_method=oc.get("shipping_method", "standard"),
                shipping_address_country=oc.get("shipping_address_country", "US"),
                shipping_address_state=oc.get("shipping_address_state"),
                seller_type=oc.get("seller_type", "direct"),
                seller_name=oc.get("seller_name"),
            )

        ticket = TicketInput(
            ticket_id=entry["ticket_id"],
            customer_name=entry["customer_name"],
            customer_email=entry.get("customer_email", ""),
            customer_tier=entry.get("customer_tier", "bronze"),
            ticket_text=entry["ticket_text"],
            order_context=order_ctx,
        )
        tickets.append(ticket)

    return tickets


def compute_metrics(results: list[dict]) -> dict:
    """Compute evaluation metrics from results."""
    total = len(results)
    if total == 0:
        return {}

    # Citation coverage rate
    with_citations = sum(1 for r in results if r.get("citations") and len(r["citations"]) > 0)
    citation_rate = (with_citations / total) * 100

    # Compliance pass rate
    approved = sum(1 for r in results if r.get("compliance_status") == "approved")
    compliance_rate = (approved / total) * 100

    # Escalation rate
    escalated = sum(1 for r in results if r.get("requires_escalation"))
    escalation_rate = (escalated / total) * 100

    # Rewrite rate
    rewrites = sum(1 for r in results if r.get("rewrite_count", 0) > 0)
    rewrite_rate = (rewrites / total) * 100

    # Average rewrite count (for non-zero)
    rewrite_counts = [r.get("rewrite_count", 0) for r in results if r.get("rewrite_count", 0) > 0]
    avg_rewrites = sum(rewrite_counts) / len(rewrite_counts) if rewrite_counts else 0

    # Error rate
    errors = sum(1 for r in results if r.get("error"))
    error_rate = (errors / total) * 100

    return {
        "total_tickets": total,
        "citation_coverage_rate": round(citation_rate, 1),
        "compliance_pass_rate": round(compliance_rate, 1),
        "escalation_rate": round(escalation_rate, 1),
        "rewrite_rate": round(rewrite_rate, 1),
        "avg_rewrites_when_needed": round(avg_rewrites, 2),
        "error_rate": round(error_rate, 1),
        "tickets_approved": approved,
        "tickets_escalated": escalated,
        "tickets_with_citations": with_citations,
        "tickets_with_errors": errors,
    }


def safe_print(text: str):
    """Print text safely on Windows by replacing non-ASCII characters."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def clean_field(raw, default="unknown") -> str:
    """Extract a single clean value from raw multi-line agent output.

    The Triage Agent may return structured text like:
        'refund\nSUB_CATEGORY: damaged_item\nPRIORITY: medium\n...'
    This function reduces it to just the first meaningful token: 'refund'.
    """
    if not raw:
        return default
    first = str(raw).strip().split("\n")[0].strip()
    for prefix in ["ISSUE_TYPE:", "PRIORITY:", "STATUS:", "TYPE:", "CATEGORY:"]:
        if first.upper().startswith(prefix):
            first = first[len(prefix):].strip()
    first = first.split()[0] if first else default
    return first.replace("_", " ").title()



def run_evaluation(
    tickets_path: str = None,
    max_tickets: int = None,
    output_dir: str = None,
):
    """
    Run the full evaluation pipeline.

    Args:
        tickets_path: Path to test tickets JSON
        max_tickets: Maximum number of tickets to process (for quick testing)
        output_dir: Directory to save results
    """
    # Defaults
    if tickets_path is None:
        tickets_path = os.path.join(os.path.dirname(__file__), "test_tickets.json")
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation_results")

    os.makedirs(output_dir, exist_ok=True)

    # Validate API key
    settings.validate()

    safe_print("=" * 80)
    safe_print("  ResolveAI - Evaluation Suite")
    safe_print(f"  Model: {settings.LLM_MODEL}")
    safe_print("=" * 80)
    safe_print("")

    # Step 1: Build vector store
    safe_print("Step 1: Building vector store from policy documents...")
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
    store.build_index(chunks)
    store.save()
    safe_print("")

    # Step 2: Initialize orchestrator with the correct provider
    safe_print("Step 2: Initializing agent orchestrator...")
    orchestrator = SupportOrchestrator(
        google_api_key=settings.GOOGLE_API_KEY,
        groq_api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        vector_store=store,
    )
    safe_print("")

    # Step 3: Load test tickets
    safe_print("Step 3: Loading test tickets...")
    tickets = load_test_tickets(tickets_path)
    if max_tickets:
        tickets = tickets[:max_tickets]
    safe_print(f"   Loaded {len(tickets)} tickets\n")

    # Step 4: Process each ticket
    results = []
    for i, ticket in enumerate(tickets, 1):
        safe_print(f"\n{'#' * 80}")
        safe_print(f"## Ticket {i}/{len(tickets)}: {ticket.ticket_id}")
        safe_print(f"{'#' * 80}")

        start_time = time.time()
        try:
            resolution = orchestrator.resolve_ticket(ticket)
            elapsed = time.time() - start_time

            result = {
                "ticket_id": resolution.ticket_id,
                "issue_type": resolution.issue_type,
                "priority": resolution.priority,
                "customer_response": resolution.customer_response,
                "internal_notes": resolution.internal_notes,
                "actions_to_take": resolution.actions_to_take,
                "citations": resolution.citations,
                "compliance_status": resolution.compliance_status,
                "requires_escalation": resolution.requires_escalation,
                "escalation_reason": resolution.escalation_reason,
                "rewrite_count": resolution.rewrite_count,
                "processing_time_seconds": round(elapsed, 2),
                "error": None,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            result = {
                "ticket_id": ticket.ticket_id,
                "issue_type": "error",
                "priority": "high",
                "customer_response": "",
                "internal_notes": f"Error: {str(e)}",
                "actions_to_take": [],
                "citations": [],
                "compliance_status": "error",
                "requires_escalation": True,
                "escalation_reason": f"Processing error: {str(e)}",
                "rewrite_count": 0,
                "processing_time_seconds": round(elapsed, 2),
                "error": str(e),
            }
            safe_print(f"Error processing {ticket.ticket_id}: {e}")

        results.append(result)

        # Print quick summary
        issue_clean   = clean_field(result.get("issue_type"))
        priority_clean = clean_field(result.get("priority"))
        safe_print(
            f"\nResult: {result['compliance_status']} | "
            f"Issue: {issue_clean} | "
            f"Priority: {priority_clean} | "
            f"Escalated: {result['requires_escalation']} | "
            f"Citations: {len(result['citations'])} | "
            f"Rewrites: {result['rewrite_count']} | "
            f"Time: {result['processing_time_seconds']}s"
        )

        # Rate limit delay between tickets (skip after last)
        if i < len(tickets):
            safe_print(f"   Waiting {INTER_TICKET_DELAY}s to avoid rate limits...")
            time.sleep(INTER_TICKET_DELAY)

    # Step 5: Compute metrics
    safe_print(f"\n{'=' * 80}")
    safe_print("EVALUATION RESULTS")
    safe_print(f"{'=' * 80}\n")

    metrics = compute_metrics(results)
    for key, value in metrics.items():
        label = key.replace("_", " ").title()
        safe_print(f"  {label}: {value}{'%' if 'rate' in key else ''}")

    # Step 6: Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results_path = os.path.join(output_dir, f"results_{timestamp}.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "results": results}, f, indent=2, ensure_ascii=True)
    safe_print(f"\nResults saved to {results_path}")

    # Save a readable report
    report_path = os.path.join(output_dir, f"report_{timestamp}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        def report_write(text):
            f.write(text.replace("—", "-"))

        report_write("# Evaluation Report\n\n")
        report_write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_write(f"**Model:** {settings.LLM_MODEL}\n")
        report_write(f"**Tickets Processed:** {metrics['total_tickets']}\n\n")
        report_write("## Metrics\n\n")
        report_write(f"| Metric | Value |\n|--------|-------|\n")
        for key, value in metrics.items():
            label = key.replace("_", " ").title()
            report_write(f"| {label} | {value}{'%' if 'rate' in key else ''} |\n")
        report_write("\n## Ticket Results\n\n")
        for result in results:
            issue_clean    = clean_field(result.get("issue_type"))
            priority_clean = clean_field(result.get("priority"))
            report_write(f"### {result['ticket_id']}\n")
            report_write(f"- **Issue Type:** {issue_clean}\n")
            report_write(f"- **Priority:** {priority_clean}\n")
            report_write(f"- **Compliance:** {result['compliance_status']}\n")
            report_write(f"- **Escalated:** {result['requires_escalation']}\n")
            report_write(f"- **Citations:** {len(result['citations'])}\n")
            report_write(f"- **Rewrites:** {result['rewrite_count']}\n")
            report_write(f"- **Time:** {result['processing_time_seconds']}s\n")
            if result['error']:
                report_write(f"- **Error:** {result['error']}\n")
            
            # Sanitize customer response for safe ASCII representation
            resp = result['customer_response'].replace("—", "-").encode('ascii', errors='replace').decode('ascii')
            report_write(f"\n**Customer Response:**\n\n{resp}\n\n---\n\n")
    safe_print(f"Report saved to {report_path}")

    return metrics, results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate the Support Resolution Agent")
    parser.add_argument("--tickets", type=str, help="Path to test tickets JSON")
    parser.add_argument("--max", type=int, help="Max tickets to process")
    parser.add_argument("--output", type=str, help="Output directory")
    args = parser.parse_args()

    run_evaluation(
        tickets_path=args.tickets,
        max_tickets=args.max,
        output_dir=args.output,
    )
