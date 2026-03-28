"""
Resolution Writer Agent — Drafts customer-facing responses based on retrieved policies.
Third agent in the pipeline. Must only use retrieved evidence.
"""

from typing import Any
from crewai import Agent, Task


def create_resolution_agent(llm: Any) -> Agent:
    """Create the Resolution Writer Agent."""
    return Agent(
        role="Customer Resolution Writer",
        goal="Draft empathetic, policy-compliant customer responses using retrieved evidence.",
        backstory=(
            "You are a resolution writer. You craft clear responses "
            "based strictly on policy citations. You explain policies simply."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        use_system_prompt=False,
    )


def create_resolution_task(
    agent: Agent,
    ticket_text: str,
    triage_summary: str,
    issue_type: str,
    customer_name: str,
    customer_tier: str,
    policy_excerpts: str,
) -> Task:
    """Create the resolution writing task."""
    return Task(
        description=f"""Draft a customer-facing resolution response for the following support ticket.

## Original Ticket
{ticket_text}

## Triage Summary
{triage_summary}

## Issue Type: {issue_type}
## Customer Name: {customer_name}
## Customer Tier: {customer_tier}

## Retrieved Policy Excerpts
{policy_excerpts}

## Guidelines
1. **Tone**: Warm and professional.
2. **Body**: Empathize, state resolution, and cite specific policies.
3. **Next Steps**: Clearly outline actions needed.

## Critical Rules
- **ONLY use information from the retrieved policy excerpts.** Do NOT invent policies or make assumptions.
- **If a policy doesn't cover the situation,** explicitly state: "This specific situation is not covered in our current policies, and I'm escalating this to a specialist team."
- **Cite sources** in brackets, e.g., [Returns & Refunds Policy — Section 3.2]
- **Be specific about timelines** (use exact numbers from the policy, e.g., "5-7 business days")
- **Consider the customer's loyalty tier** — {customer_tier} members may have special benefits
- **Never share internal-only information** with the customer (internal escalation procedures, agent authority levels, fraud scores)

## Output Format

CUSTOMER_RESPONSE:
[The complete customer-facing email/message]

INTERNAL_NOTES:
[Notes for the support team about this resolution — not visible to customer]

CRITICAL_ACTIONS:
[Numbered list of immediate system/agent actions, e.g., "1. Trigger Refund $X", "2. Issue RMA", "3. Escalate to QA"]

CITATIONS_USED:
[List all policy citations referenced in the response]
""",
        expected_output=(
            "A complete customer-facing response with policy citations, "
            "internal notes, a structured list of CRITICAL ACTIONS, and a citation list."
        ),
        agent=agent,
    )
