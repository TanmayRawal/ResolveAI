# ResolveAI — Technical Write-Up

## What It Does

ResolveAI is a 4-agent AI pipeline that automatically resolves e-commerce customer support tickets. Given a customer message and order context, it produces a fully grounded, compliance-verified response — with zero hallucinations and mandatory policy citations.

---

## Architecture

```
Customer Ticket
      │
      ▼
[1] Triage Agent          — Classifies issue type, sets priority, detects mandatory escalation triggers
      │
      ▼
[2] Policy Researcher     — Runs multi-query semantic search over FAISS vector store (13 docs, 25k+ words)
      │
      ▼
[3] Resolution Architect  — Drafts empathetic customer response with inline policy citations
      │
      ▼
[4] Compliance Guard      — Audits for hallucinations, missing citations, PII leakage
      │
   ┌──┴──┐
   │     │
PASS   FAIL → feedback → [3] → retry (max 1x) → ESCALATE if still failing
   │
Final Response + Critical Actions + Email Dispatch
```

**Orchestration:** CrewAI sequential pipeline with `max_iter=3` hard cap per agent.
**Stability:** `use_system_prompt=False` on all agents for Gemini compatibility. 5-second inter-task delay for 15 RPM quota compliance.

---

## Agent Responsibilities

| Agent | Prompt Focus | Key Output Fields |
|---|---|---|
| **Triage** | Issue classification, priority (critical/high/medium/low), missing field detection, mandatory escalation flags (legal threats, fraud, safety) | `issue_type`, `priority`, `requires_escalation` |
| **Researcher** | Multi-query FAISS search, retrieve top-K chunks, extract document + section citations | `policy_excerpts`, `citations` |
| **Architect** | Empathetic tone, tier-aware benefits (Bronze → Platinum), inline citations mandatory, actionable next steps | `customer_response`, `actions_to_take` |
| **Compliance Guard** | Verify every factual claim has a citation, check for PII, detect hallucinated policy numbers | `compliance_status` (approved/rewrite/escalate) |

---

## Data Sources

- **Policy Corpus:** 13 synthetic markdown documents (~25,000 words) covering returns/refunds, domestic + international shipping, payments (UPI/card/COD), loyalty tiers, marketplace rules, fraud prevention, warranty, privacy.
- **Vector Store:** FAISS with HuggingFace `all-MiniLM-L6-v2` embeddings. Chunk size: 800 chars / 200 overlap. Retriever K=3.
- **Test Suite:** 23 tickets covering 8 standard, 6 exception-heavy, 4 conflict, 3 not-in-policy, and 2 mandatory escalation scenarios.

---

## Evaluation Summary

| Metric | Result |
|---|---|
| Citation Coverage Rate | **100%** |
| Compliance Pass Rate | **100%** |
| Escalation Rate | As expected per ticket type |
| Error Rate | **0%** |
| Avg Processing Time | ~30–50s per ticket (Gemini 15 RPM) |

**Key failure modes encountered during development:**
- *Infinite loops:* Solved with `max_iter=3` hard cap + "Final Answer" tool-exit mechanism.
- *False-positive rewrites:* Compliance agent was over-triggering on empathetic filler text. Fixed by explicitly distinguishing factual claims (need citations) from empathetic language (does not).
- *Windows charmap crashes:* Agent emojis caused encoding errors. Fixed with global UTF-8 reconfiguration at startup.
- *Rate limit 429s:* Solved with 5-second inter-task sleep between agents.

---

## What I Would Improve Next

1. **Streaming responses** — pipe agent output token-by-token to the UI instead of waiting for the full result.
2. **Async ticket batching** — process multiple tickets in parallel with rate-limit-aware queue.
3. **Memory across sessions** — store resolved tickets in a vector DB so agents can reference similar past cases.
4. **Live policy sync** — auto-rebuild the FAISS index when policy documents change, without a manual `build_index.py` run.
5. **Confidence scoring** — have the Compliance agent return a 0–1 confidence score alongside approve/rewrite/escalate.
