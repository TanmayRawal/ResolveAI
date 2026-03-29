# Example Runs — ResolveAI

Three documented end-to-end resolutions demonstrating the system's ability to handle exception, conflict+escalation, and abstention scenarios.

---

## Run 1 — Exception Handled Correctly

**Scenario:** Customer wants to return opened swimwear (non-returnable category), but hasn't worn it outside.

**Input:**
```json
{
  "ticket_id": "TKT-005",
  "customer_name": "Ananya Singh",
  "customer_tier": "bronze",
  "ticket_text": "Maine ek week pehle swimsuit kharida tha par size galat hai. Tags nahi utaare, ghar mein sirf try on kiya. Exchange chahiye. Lekin site par swimwear non-returnable likha hai. Maine bahar kahi nahi pehna, yeh toh unfair hai.",
  "order_context": {
    "order_id": "ORD-2026-44890",
    "order_date": "2026-03-21",
    "delivery_date": "2026-03-25",
    "items": [{"name": "AquaFit One-Piece Swimsuit - Medium", "price": 1999.00}],
    "total_amount": 2199.00,
    "payment_method": "upi"
  }
}
```

**Agent Pipeline Output:**

| Agent | Result |
|---|---|
| Triage | `issue_type: return_request` · `priority: medium` · `requires_escalation: false` |
| Researcher | Retrieved `returns_refunds.md §4.2 Non-Returnable Items`, `returns_refunds.md §3.1 Return Eligibility` |
| Architect | Drafted response acknowledging the exception request, citing the non-returnable policy, and offering a size guide or store credit alternative |
| Compliance | **APPROVED** — all claims cited, no PII, no hallucinations |

**Customer Response (excerpt):**
> Dear Ananya, thank you for reaching out. We understand how frustrating it is when a size doesn't fit as expected. Our swimwear category is marked non-returnable once unsealed, in line with hygiene standards [returns_refunds.md — 4.2 Non-Returnable Items]. However, because the item was only tried on indoors with tags intact, we'd like to offer you a **one-time size exchange** as a goodwill gesture. Please contact us with your preferred size and we'll arrange a replacement shipment [returns_refunds.md — 3.1 Return Eligibility: Special Discretion].

**Citations:** `returns_refunds.md — 4.2 Non-Returnable Items`, `returns_refunds.md — 3.1 Return Eligibility`
**Compliance:** ✅ Approved · Rewrites: 0

---

## Run 2 — Conflict Handled with Escalation

**Scenario:** Customer reports fraudulent charges and potential account compromise — mandatory escalation trigger.

**Input:**
```json
{
  "ticket_id": "TKT-006",
  "customer_name": "Vikram Nair",
  "customer_tier": "bronze",
  "ticket_text": "Mere credit card par ₹28,999 aur ₹17,999 ke do charges dikh rahe hain, lekin maine sirf ek order ₹28,999 ka kiya tha. Doosra purchase maine nahi kiya. Kisi ne mera account hack kiya hoga. Turant investigate karo.",
  "order_context": {
    "order_id": "ORD-2026-45901",
    "order_date": "2026-03-26",
    "items": [{"name": "Sony Wireless Noise-Canceling Headphones", "price": 24999.00}],
    "total_amount": 28999.00,
    "payment_method": "credit_card"
  }
}
```

**Agent Pipeline Output:**

| Agent | Result |
|---|---|
| Triage | `issue_type: fraud` · `priority: critical` · `requires_escalation: TRUE` · reason: "Unauthorized charges and suspected account compromise — mandatory fraud escalation" |
| Researcher | Retrieved `fraud_prevention.md §2.1 Unauthorized Charges`, `fraud_prevention.md §3.2 Account Security`, `payment_policy.md §5.1 Dispute Resolution` |
| Architect | Drafted empathetic response acknowledging the severity, explaining the fraud investigation process, providing immediate next steps |
| Compliance | **APPROVED** — escalation correctly flagged |

**Customer Response (excerpt):**
> Dear Vikram, we take reports of unauthorized charges extremely seriously. Your account has been flagged for an immediate security review [fraud_prevention.md — 3.2 Account Security]. Our Fraud Investigation Team will contact you within 2 business hours. In the meantime, we strongly recommend changing your account password and enabling two-factor authentication [fraud_prevention.md — 2.1 Unauthorized Charges].

**Citations:** `fraud_prevention.md — 2.1`, `fraud_prevention.md — 3.2`, `payment_policy.md — 5.1`
**Compliance:** ✅ Approved · **Escalated: YES** · Rewrites: 0

---

## Run 3 — Correct Abstention ("Need More Info" / Not-in-Policy)

**Scenario:** Customer asks about paying with cryptocurrency — a payment method not covered in any policy document.

**Input:**
```json
{
  "ticket_id": "TKT-012",
  "customer_name": "Suresh Pillai",
  "customer_tier": "bronze",
  "ticket_text": "Kya main crypto se gaming PC khareed sakta hoon? Aur agar crypto se payment kiya aur return karna pada toh refund kaisa hoga?",
  "order_context": null
}
```

**Agent Pipeline Output:**

| Agent | Result |
|---|---|
| Triage | `issue_type: payment_inquiry` · `priority: low` · `requires_escalation: false` |
| Researcher | Searched all payment policy documents — no results for cryptocurrency payments |
| Architect | Drafted honest response: cryptocurrency not a supported payment method, listed what IS supported, offered to help with available options |
| Compliance | **APPROVED** — correctly abstains from inventing policy, no hallucinated claims |

**Customer Response (excerpt):**
> Dear Suresh, thank you for your question. At this time, cryptocurrency is not a supported payment method on our platform [payment_policy.md — 2.1 Accepted Payment Methods]. We currently accept UPI, Credit/Debit Cards, Net Banking, and Cash on Delivery. If the item is eligible, EMI options are also available on select cards. We'd be happy to help you place your order using any of these methods!

**Citations:** `payment_policy.md — 2.1 Accepted Payment Methods`
**Compliance:** ✅ Approved · Rewrites: 0 · **Correct Abstention — no policy invented**

---

## Summary

| Run | Scenario Type | Compliance | Escalated | Citations | Rewrites |
|---|---|---|---|---|---|
| Run 1 (TKT-005) | Exception — non-returnable category | ✅ Approved | No | 2 | 0 |
| Run 2 (TKT-006) | Conflict — fraud + unauthorized charge | ✅ Approved | **Yes** | 3 | 0 |
| Run 3 (TKT-012) | Not-in-policy — crypto payment | ✅ Approved | No | 1 | 0 |
