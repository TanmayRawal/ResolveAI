"""
Pydantic data models for the E-commerce Support Resolution Agent.
Defines structured inputs and outputs for all agents in the pipeline.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IssueType(str, Enum):
    """Classification categories for support tickets."""
    REFUND = "refund"
    RETURN = "return"
    SHIPPING = "shipping"
    PAYMENT = "payment"
    PROMO = "promo"
    FRAUD = "fraud"
    WARRANTY = "warranty"
    CANCELLATION = "cancellation"
    MARKETPLACE = "marketplace"
    ACCOUNT = "account"
    OTHER = "other"


class CustomerTier(str, Enum):
    """Customer loyalty tiers."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class OrderItem(BaseModel):
    """An item in a customer order."""
    name: str = Field(description="Product name")
    sku: str = Field(default="", description="Product SKU")
    category: str = Field(default="", description="Product category")
    price: float = Field(description="Price paid for the item")
    quantity: int = Field(default=1, description="Quantity purchased")


class OrderContext(BaseModel):
    """Structured order context accompanying a support ticket."""
    order_id: str = Field(description="Order identifier")
    order_date: str = Field(description="Date the order was placed (YYYY-MM-DD)")
    delivery_date: Optional[str] = Field(default=None, description="Actual delivery date, if delivered")
    estimated_delivery: Optional[str] = Field(default=None, description="Estimated delivery date")
    items: list[OrderItem] = Field(default_factory=list, description="Items in the order")
    total_amount: float = Field(description="Total order amount")
    payment_method: str = Field(default="credit_card", description="Payment method used")
    shipping_method: str = Field(default="standard", description="Shipping method selected")
    shipping_address_country: str = Field(default="US", description="Shipping destination country")
    shipping_address_state: Optional[str] = Field(default=None, description="State/region")
    seller_type: str = Field(default="direct", description="1P, FBS, or 3P")
    seller_name: Optional[str] = Field(default=None, description="Seller name for marketplace orders")


class TicketInput(BaseModel):
    """Input model for a customer support ticket."""
    ticket_id: str = Field(description="Unique ticket identifier")
    customer_name: str = Field(description="Customer's name")
    customer_email: str = Field(default="", description="Customer email")
    customer_tier: CustomerTier = Field(default=CustomerTier.BRONZE, description="Loyalty tier")
    ticket_text: str = Field(description="Free-form ticket/complaint text from the customer")
    order_context: Optional[OrderContext] = Field(default=None, description="Structured order data")


class TriageOutput(BaseModel):
    """Output from the Triage Agent."""
    issue_type: str = Field(description="Classified issue type")
    sub_category: str = Field(default="", description="More specific sub-category")
    priority: str = Field(default="medium", description="Priority: low, medium, high, urgent")
    missing_fields: list[str] = Field(default_factory=list, description="Information still needed")
    clarifying_questions: list[str] = Field(default_factory=list, description="Questions to ask the customer")
    summary: str = Field(description="Brief summary of the issue for downstream agents")
    requires_escalation: bool = Field(default=False, description="Whether manual escalation is needed")
    escalation_reason: str = Field(default="", description="Reason for escalation if applicable")


class PolicyExcerpt(BaseModel):
    """A retrieved policy excerpt with citation."""
    content: str = Field(description="Text content of the policy excerpt")
    source_document: str = Field(description="Source document filename/title")
    section: str = Field(default="", description="Section heading or ID")
    relevance_score: float = Field(default=0.0, description="Similarity score from retrieval")


class RetrieverOutput(BaseModel):
    """Output from the Policy Retriever Agent."""
    retrieved_policies: list[PolicyExcerpt] = Field(default_factory=list, description="Retrieved policy excerpts")
    search_queries_used: list[str] = Field(default_factory=list, description="Queries used for retrieval")


class ResolutionOutput(BaseModel):
    """Output from the Resolution Writer Agent."""
    customer_response: str = Field(description="Draft customer-facing response")
    internal_notes: str = Field(default="", description="Internal notes for the support team")
    actions_to_take: list[str] = Field(default_factory=list, description="Actions the system should take")
    citations: list[str] = Field(default_factory=list, description="Policy citations used")


class ComplianceResult(BaseModel):
    """Output from the Compliance/Safety Agent."""
    is_compliant: bool = Field(description="Whether the response passes compliance checks")
    issues_found: list[str] = Field(default_factory=list, description="Issues identified")
    unsupported_claims: list[str] = Field(default_factory=list, description="Claims without policy backing")
    missing_citations: list[str] = Field(default_factory=list, description="Statements needing citations")
    sensitive_data_detected: bool = Field(default=False, description="Whether PII/sensitive data was found")
    recommendation: str = Field(default="approve", description="approve, rewrite, or escalate")
    rewrite_instructions: str = Field(default="", description="Instructions for rewriting if needed")


class FinalResolution(BaseModel):
    """Final output of the complete pipeline."""
    ticket_id: str
    issue_type: str
    priority: str
    customer_response: str
    internal_notes: str
    actions_to_take: list[str]
    citations: list[str]
    compliance_status: str
    requires_escalation: bool
    escalation_reason: str = ""
    rewrite_count: int = Field(default=0, description="Number of compliance rewrites performed")
