"""
Compliance / Safety Agent — Validates responses for policy compliance and safety.
Fourth and final agent in the pipeline. Catches hallucinations and unsafe outputs.
"""

from typing import Any
from crewai import Agent, Task


def create_compliance_agent(llm: Any) -> Agent:
    """Create the Compliance / Safety Agent."""
    return Agent(
        role="Compliance & Safety Auditor",
        goal="Audit responses for policy accuracy, citations, and hallucination.",
        backstory=(
            "You are a compliance auditor. You ensure all claims are "
            "backed by citations and filter out sensitive data."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        use_system_prompt=False,
    )


def create_compliance_task(
    agent: Agent,
    customer_response: str,
    policy_excerpts: str,
    issue_type: str,
    customer_tier: str,
) -> Task:
    """Create the compliance review task."""
    return Task(
        description=f"""Audit the following customer-facing response for compliance and safety.

## Customer Response to Audit
{customer_response}

## Policy Excerpts Available (Ground Truth)
{policy_excerpts}

## Issue Type: {issue_type}
## Customer Tier: {customer_tier}

## Audit Checklist
1. **Source Check**: Does the response only use the provided policy excerpts?
2. **Citations (Critical)**: Are all *factual policy claims* accurately cited (doc + section)? (e.g., refund eligibility, timelines).
3. **No Over-Audit**: Do NOT flag empathetic or transitional sentences for missing citations (e.g., "I'm sorry to hear that").
4. **Accuracy**: Are timelines and facts consistent with policies?
5. **Security**: Is there any PII or internal data?
6. **Escalate**: Only flag for human review if there is a major policy violation or inaccurate information.

## Output Format

IS_COMPLIANT: [true/false]

ISSUES_FOUND:
[Numbered list of specific issues, or "None"]

UNSUPPORTED_CLAIMS:
[List of claims in the response that are not backed by the provided policies, or "None"]

MISSING_CITATIONS:
[List of statements that should have citations but don't, or "None"]

SENSITIVE_DATA_DETECTED: [true/false]
SENSITIVE_DATA_DETAILS: [What was found, or "N/A"]

RECOMMENDATION: [approve / rewrite / escalate]

REWRITE_INSTRUCTIONS:
[If recommendation is "rewrite", provide specific instructions on what to fix.
If recommendation is "approve", write "N/A".
If recommendation is "escalate", explain why human review is needed.]
""",
        expected_output=(
            "A complete compliance audit with findings on unsupported claims, "
            "missing citations, sensitive data, and a clear recommendation "
            "(approve, rewrite, or escalate)."
        ),
        agent=agent,
    )
