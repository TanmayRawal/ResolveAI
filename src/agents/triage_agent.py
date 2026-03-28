"""
Triage Agent — Classifies support tickets and extracts key information.
First agent in the pipeline. Determines issue type, priority, and missing fields.
"""

from typing import Any
from crewai import Agent, Task


def create_triage_agent(llm: Any) -> Agent:
    """Create the Triage Agent."""
    return Agent(
        role="Customer Support Triage Specialist",
        goal="Classify tickets by type and priority, identifying missing info.",
        backstory=(
            "You are a triage specialist. You quickly identify the core issue, "
            "assess urgency, and note missing data for efficient resolution."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        use_system_prompt=False,
    )


def create_triage_task(agent: Agent, ticket_text: str, order_context_str: str, customer_tier: str) -> Task:
    """Create the triage task for a given ticket."""
    return Task(
        description=f"""Analyze the following customer support ticket and provide a structured triage assessment.

## Customer Information
- **Loyalty Tier:** {customer_tier}

## Ticket Text
{ticket_text}

## Order Context
{order_context_str}

## Your Task
1. **Classify type**: refund, return, shipping, payment, promo, fraud, warranty, cancellation, marketplace, account, other
2. **Category**: e.g., "damaged_item", "late_delivery"
3. **Priority**: low, medium, high, urgent (Urgent for safety/fraud/legal)
4. **Missing fields**: What's needed but missing?
5. **Summary**: 2-3 sentence overview for retrieval.
6. **Escalate**: Flag if legal/safety/fraud issues present.

## Output Format
Provide your response in this exact format:

ISSUE_TYPE: [type]
SUB_CATEGORY: [sub-category]
PRIORITY: [low/medium/high/urgent]
MISSING_FIELDS: [comma-separated list, or "none"]
CLARIFYING_QUESTIONS: [numbered list, or "none"]
SUMMARY: [2-3 sentence summary of the issue for downstream agents]
REQUIRES_ESCALATION: [true/false]
ESCALATION_REASON: [reason if true, or "N/A"]
""",
        expected_output=(
            "A structured triage assessment with issue type, priority, missing fields, "
            "clarifying questions, summary, and escalation flag."
        ),
        agent=agent,
    )
