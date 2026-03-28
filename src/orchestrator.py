"""
Orchestrator — CrewAI-based pipeline that coordinates all 4 agents.
Manages the flow: Triage → Retrieval → Resolution → Compliance.
Includes retry logic for compliance rewrites.
"""

import json
import re
import time
from crewai import Crew, Process, LLM
from src.models import TicketInput, FinalResolution
from src.vectorstore.store import PolicyVectorStore
from src.agents.triage_agent import create_triage_agent, create_triage_task
from src.agents.retriever_agent import create_retriever_agent, create_retriever_task
from src.agents.resolution_agent import create_resolution_agent, create_resolution_task
from src.agents.compliance_agent import create_compliance_agent, create_compliance_task


class SupportOrchestrator:
    """
    Orchestrates the multi-agent support resolution pipeline.

    Flow:
    1. Triage Agent → Classifies and summarizes the ticket
    2. Policy Retriever Agent → Finds relevant policies
    3. Resolution Writer Agent → Drafts the customer response
    4. Compliance Agent → Audits the response
    5. If compliance fails → Resolution Writer rewrites (max 2 retries)
    """

    MAX_REWRITES = 1

    def __init__(self, google_api_key: str = None, groq_api_key: str = None, model: str = "gemini/gemini-1.5-flash-latest", vector_store: PolicyVectorStore = None):
        """
        Initialize the orchestrator with the appropriate LLM provider.

        Args:
            google_api_key: Google Gemini API key
            groq_api_key: Groq API key
            model: Model name (e.g. gemini/... or groq/...)
            vector_store: Initialized PolicyVectorStore instance
        """
        self.google_api_key = google_api_key
        self.groq_api_key = groq_api_key
        self.current_model = model

        # Determine which API key to use based on the model prefix
        primary_api_key = groq_api_key if model.startswith("groq/") else google_api_key

        self.llm = LLM(
            model=model,
            api_key=primary_api_key,
            temperature=0.1,
            max_tokens=2048,
        )

        self.vector_store = vector_store

        # Create agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agents with the current LLM."""
        self.triage_agent = create_triage_agent(self.llm)
        self.retriever_agent, self.search_tool = create_retriever_agent(self.llm, self.vector_store)
        self.resolution_agent = create_resolution_agent(self.llm)
        self.compliance_agent = create_compliance_agent(self.llm)

    def _safe_kickoff(self, crew: Crew) -> str:
        """
        Execute a crew kickoff with proactive pacing to avoid Rate Limits.
        """
        print("API Pacing (Stable 3.1): Waiting 5 seconds for Gemini 3.1 Flash Lite...")
        time.sleep(5)
        return str(crew.kickoff())

    def resolve_ticket(self, ticket: TicketInput) -> FinalResolution:
        """
        Process a support ticket through the full pipeline.

        Args:
            ticket: TicketInput model with ticket details

        Returns:
            FinalResolution with the complete resolution output
        """
        print(f"\n{'='*80}")
        print(f"Processing Ticket: {ticket.ticket_id}")
        print(f"{'='*80}\n")

        # Prepare order context string
        order_context_str = self._format_order_context(ticket)

        # Step 1: Triage
        print("> Step 1: TRIAGE")
        triage_task = create_triage_task(
            self.triage_agent,
            ticket.ticket_text,
            order_context_str,
            ticket.customer_tier.value,
        )
        triage_crew = Crew(
            agents=[self.triage_agent],
            tasks=[triage_task],
            process=Process.sequential,
            verbose=True,
        )
        triage_result = self._safe_kickoff(triage_crew)
        triage_parsed = self._parse_triage_output(triage_result)
        print(f"Triage complete - Issue: {triage_parsed['issue_type']}, Priority: {triage_parsed['priority']}\n")

        # Check for mandatory escalation
        if triage_parsed.get("requires_escalation"):
            return self._create_escalation_resolution(ticket, triage_parsed)

        # Step 2: Policy Retrieval
        print("> Step 2: POLICY RETRIEVAL")
        self.search_tool.search_count = 0  # Reset token-limit tool breaker switch for the new ticket
        retriever_task = create_retriever_task(
            self.retriever_agent,
            triage_parsed["summary"],
            triage_parsed["issue_type"],
            ticket.customer_tier.value,
        )
        retriever_crew = Crew(
            agents=[self.retriever_agent],
            tasks=[retriever_task],
            process=Process.sequential,
            verbose=True,
        )
        policy_excerpts = self._safe_kickoff(retriever_crew)
        print(f"Policy retrieval complete\n")

        # ── Step 3 & 4: Resolution + Compliance (with retry loop) ──
        rewrite_count = 0
        rewrite_instructions = ""

        while rewrite_count <= self.MAX_REWRITES:
            # Step 3: Resolution Writing
            print(f"> Step 3: RESOLUTION WRITING {'(REWRITE #' + str(rewrite_count) + ')' if rewrite_count > 0 else ''}")

            # Append rewrite instructions if this is a retry
            extra_instructions = ""
            if rewrite_instructions:
                extra_instructions = f"\n\n## COMPLIANCE REWRITE REQUIRED\nThe previous response was flagged by the compliance team. Fix these issues:\n{rewrite_instructions}"

            resolution_task = create_resolution_task(
                self.resolution_agent,
                ticket.ticket_text + extra_instructions,
                triage_parsed["summary"],
                triage_parsed["issue_type"],
                ticket.customer_name,
                ticket.customer_tier.value,
                policy_excerpts,
            )
            resolution_crew = Crew(
                agents=[self.resolution_agent],
                tasks=[resolution_task],
                process=Process.sequential,
                verbose=True,
            )
            resolution_result = self._safe_kickoff(resolution_crew)
            resolution_parsed = self._parse_resolution_output(resolution_result)
            print(f"Resolution draft complete\n")

            # Step 4: Compliance Check
            print("> Step 4: COMPLIANCE CHECK")
            compliance_task = create_compliance_task(
                self.compliance_agent,
                resolution_parsed["customer_response"],
                policy_excerpts,
                triage_parsed["issue_type"],
                ticket.customer_tier.value,
            )
            compliance_crew = Crew(
                agents=[self.compliance_agent],
                tasks=[compliance_task],
                process=Process.sequential,
                verbose=True,
            )
            compliance_result = self._safe_kickoff(compliance_crew)
            compliance_parsed = self._parse_compliance_output(compliance_result)
            print(f"Compliance check complete - Recommendation: {compliance_parsed['recommendation']}\n")

            if compliance_parsed["recommendation"] == "approve":
                return FinalResolution(
                    ticket_id=ticket.ticket_id,
                    issue_type=triage_parsed["issue_type"],
                    priority=triage_parsed["priority"],
                    customer_response=resolution_parsed["customer_response"],
                    internal_notes=resolution_parsed.get("internal_notes", ""),
                    actions_to_take=resolution_parsed.get("actions_to_take", []),
                    citations=resolution_parsed.get("citations", []),
                    compliance_status="approved",
                    requires_escalation=False,
                    rewrite_count=rewrite_count,
                )
            elif compliance_parsed["recommendation"] == "escalate":
                return FinalResolution(
                    ticket_id=ticket.ticket_id,
                    issue_type=triage_parsed["issue_type"],
                    priority=triage_parsed["priority"],
                    customer_response=resolution_parsed["customer_response"],
                    internal_notes=f"ESCALATED: {compliance_parsed.get('rewrite_instructions', 'Compliance flagged for human review')}",
                    actions_to_take=["Escalate to human agent for review"],
                    citations=resolution_parsed.get("citations", []),
                    compliance_status="escalated",
                    requires_escalation=True,
                    escalation_reason=compliance_parsed.get("rewrite_instructions", "Compliance review required"),
                    rewrite_count=rewrite_count,
                )
            else:
                # Rewrite requested
                rewrite_instructions = compliance_parsed.get("rewrite_instructions", "Fix compliance issues")
                rewrite_count += 1
                print(f"! Compliance requested rewrite. Attempting rewrite #{rewrite_count}...\n")

        # Max rewrites exceeded — escalate
        return FinalResolution(
            ticket_id=ticket.ticket_id,
            issue_type=triage_parsed["issue_type"],
            priority=triage_parsed["priority"],
            customer_response=resolution_parsed["customer_response"],
            internal_notes=f"Max rewrites ({self.MAX_REWRITES}) exceeded. Escalating for human review.",
            actions_to_take=["Escalate to human agent — compliance could not be satisfied after max rewrites"],
            citations=resolution_parsed.get("citations", []),
            compliance_status="max_rewrites_exceeded",
            requires_escalation=True,
            escalation_reason="Compliance could not approve after maximum rewrite attempts",
            rewrite_count=rewrite_count,
        )

    def _create_escalation_resolution(self, ticket: TicketInput, triage: dict) -> FinalResolution:
        """Create a resolution that immediately escalates based on triage flags."""
        return FinalResolution(
            ticket_id=ticket.ticket_id,
            issue_type=triage["issue_type"],
            priority="urgent",
            customer_response=(
                f"Dear {ticket.customer_name},\n\n"
                "Thank you for contacting our Support team. We take your concern very seriously. "
                "Your ticket has been escalated to our specialist team for immediate review. "
                "A senior team member will contact you within 4 hours.\n\n"
                f"Your reference number is: {ticket.ticket_id}\n\n"
                "We appreciate your patience.\n\n"
                "Best regards,\nCustomer Support Team"
            ),
            internal_notes=f"MANDATORY ESCALATION: {triage.get('escalation_reason', 'Triage flagged for escalation')}",
            actions_to_take=["Immediately escalate to Level 3+ or relevant specialist team"],
            citations=[],
            compliance_status="escalated_at_triage",
            requires_escalation=True,
            escalation_reason=triage.get("escalation_reason", "Triage flagged for mandatory escalation"),
        )

    @staticmethod
    def _format_order_context(ticket: TicketInput) -> str:
        """Format order context as a readable string."""
        if ticket.order_context is None:
            return "No order context provided."

        ctx = ticket.order_context
        items_str = "\n".join(
            f"  - {item.name} (${item.price:.2f} x {item.quantity})"
            for item in ctx.items
        )
        return (
            f"Order ID: {ctx.order_id}\n"
            f"Order Date: {ctx.order_date}\n"
            f"Delivery Date: {ctx.delivery_date or 'Not yet delivered'}\n"
            f"Estimated Delivery: {ctx.estimated_delivery or 'N/A'}\n"
            f"Items:\n{items_str}\n"
            f"Total: ${ctx.total_amount:.2f}\n"
            f"Payment: {ctx.payment_method}\n"
            f"Shipping: {ctx.shipping_method}\n"
            f"Ship to: {ctx.shipping_address_state or ''}, {ctx.shipping_address_country}\n"
            f"Seller: {ctx.seller_type}"
            + (f" ({ctx.seller_name})" if ctx.seller_name else "")
        )

    @staticmethod
    def _parse_triage_output(text: str) -> dict:
        """Parse the triage agent's structured output."""
        result = {
            "issue_type": "other",
            "sub_category": "",
            "priority": "medium",
            "missing_fields": [],
            "summary": text,
            "requires_escalation": False,
            "escalation_reason": "",
        }

        patterns = {
            "issue_type": r"ISSUE_TYPE:\s*(.+)",
            "sub_category": r"SUB_CATEGORY:\s*(.+)",
            "priority": r"PRIORITY:\s*(.+)",
            "summary": r"SUMMARY:\s*(.+?)(?=\n[A-Z_]+:|$)",
            "escalation_reason": r"ESCALATION_REASON:\s*(.+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result[key] = match.group(1).strip()

        # Parse boolean escalation
        esc_match = re.search(r"REQUIRES_ESCALATION:\s*(true|false)", text, re.IGNORECASE)
        if esc_match:
            result["requires_escalation"] = esc_match.group(1).lower() == "true"

        # Parse missing fields
        mf_match = re.search(r"MISSING_FIELDS:\s*(.+)", text, re.IGNORECASE)
        if mf_match:
            fields = mf_match.group(1).strip()
            if fields.lower() != "none":
                result["missing_fields"] = [f.strip() for f in fields.split(",")]

        return result

    @staticmethod
    def _parse_resolution_output(text: str) -> dict:
        """Parse the resolution agent's structured output."""
        result = {
            "customer_response": text,
            "internal_notes": "",
            "actions_to_take": [],
            "citations": [],
        }

        # Extract customer response
        cr_match = re.search(
            r"CUSTOMER_RESPONSE:\s*(.+?)(?=INTERNAL_NOTES:|ACTIONS_TO_TAKE:|CITATIONS_USED:|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if cr_match:
            result["customer_response"] = cr_match.group(1).strip()

        # Extract internal notes
        in_match = re.search(
            r"INTERNAL_NOTES:\s*(.+?)(?=ACTIONS_TO_TAKE:|CITATIONS_USED:|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if in_match:
            result["internal_notes"] = in_match.group(1).strip()

        # Extract actions
        at_match = re.search(
            r"CRITICAL_ACTIONS:\s*(.+?)(?=CITATIONS_USED:|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if at_match:
            actions_text = at_match.group(1).strip()
            result["actions_to_take"] = [
                line.strip().lstrip("0123456789.-) ")
                for line in actions_text.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

        # Extract citations
        ci_match = re.search(r"CITATIONS_USED:\s*(.+?)$", text, re.DOTALL | re.IGNORECASE)
        if ci_match:
            citations_text = ci_match.group(1).strip()
            result["citations"] = [
                line.strip().lstrip("0123456789.-) ")
                for line in citations_text.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

        return result

    @staticmethod
    def _parse_compliance_output(text: str) -> dict:
        """Parse the compliance agent's structured output."""
        result = {
            "is_compliant": False,
            "issues_found": [],
            "unsupported_claims": [],
            "missing_citations": [],
            "sensitive_data_detected": False,
            "recommendation": "rewrite",
            "rewrite_instructions": "",
        }

        # Parse boolean fields
        comp_match = re.search(r"IS_COMPLIANT:\s*(true|false)", text, re.IGNORECASE)
        if comp_match:
            result["is_compliant"] = comp_match.group(1).lower() == "true"

        sd_match = re.search(r"SENSITIVE_DATA_DETECTED:\s*(true|false)", text, re.IGNORECASE)
        if sd_match:
            result["sensitive_data_detected"] = sd_match.group(1).lower() == "true"

        # Parse recommendation
        rec_match = re.search(r"RECOMMENDATION:\s*(approve|rewrite|escalate)", text, re.IGNORECASE)
        if rec_match:
            result["recommendation"] = rec_match.group(1).lower()

        # Parse rewrite instructions
        ri_match = re.search(
            r"REWRITE_INSTRUCTIONS:\s*(.+?)$",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if ri_match:
            result["rewrite_instructions"] = ri_match.group(1).strip()

        return result
