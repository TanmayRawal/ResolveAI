"""
Policy Retriever Agent — Queries the vector store to find relevant policy excerpts.
Second agent in the pipeline. Returns only relevant, cited excerpts.
"""

from typing import Any, Tuple
from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from src.vectorstore.store import PolicyVectorStore

class PolicySearchSchema(BaseModel):
    query: str = Field(
        ..., 
        description="The specific search phrase. MUST be a plain string. Do NOT pass a JSON object."
    )

class PolicySearchTool(BaseTool):
    """Custom CrewAI tool for searching the policy vector store."""
    
    name: str = "search_policies"
    description: str = (
        "Search the company policy database for relevant policy excerpts. "
        "Input should be a specific search query related to the customer's issue. "
        "Returns the most relevant policy excerpts with their source documents and sections."
    )
    args_schema: type[BaseModel] = PolicySearchSchema
    vector_store: PolicyVectorStore | None = None
    search_count: int = 0

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        """Execute the policy search."""
        self.search_count += 1
        if self.search_count > 1:
            return "Thought: I have already searched. I will now provide the final answer.\nFinal Answer: I have already retrieved the necessary policy excerpts in the previous step. Please refer to them."

        import time
        # Pace the API to allow Groq Token Bucket to refill during operations
        time.sleep(15)
            
        if self.vector_store is None:
            return "Error: Vector store not initialized."

        results = self.vector_store.search(query, k=3)

        if not results:
            return "No relevant policy excerpts found for this query."

        output_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            section = doc.metadata.get("section", "General")
            score = doc.metadata.get("relevance_score", 0)
            citation = doc.metadata.get("citation", source)
            
            output_parts.append(
                f"--- Excerpt {i} ---\n"
                f"Source: {source}\n"
                f"Section: {section}\n"
                f"Citation: [{citation}]\n"
                f"Relevance: {score:.3f}\n"
                f"Content:\n{doc.page_content}\n"
            )

        return "\n".join(output_parts)


def create_retriever_agent(llm: Any, vector_store: PolicyVectorStore) -> Tuple[Agent, "PolicySearchTool"]:
    """Create the Policy Retriever Agent with search tool."""
    
    search_tool = PolicySearchTool(vector_store=vector_store)

    agent = Agent(
        role="Policy Research Specialist",
        goal="Retrieve relevant policies from the database for the ticket.",
        backstory=(
            "You are a policy researcher. You quickly find policy excerpts "
            "that apply to customer issues and cite them precisely."
        ),
        llm=llm,
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        use_system_prompt=False,
    )

    return agent, search_tool


def create_retriever_task(agent: Agent, triage_summary: str, issue_type: str, customer_tier: str) -> Task:
    """Create the policy retrieval task."""
    return Task(
        description=f"""Find relevant policy excerpts for the following customer issue.

## Issue Summary (from Triage)
{triage_summary}

## Issue Type: {issue_type}
## Customer Tier: {customer_tier}

## Your Task
1. **Queries**: Use exactly 1 highly descriptive search query. NEVER execute more than one search per ticket.
2. **Search**: Find policy excerpts.
3. **Analyze**: Only include excerpts that apply to this specific issue and {customer_tier} tier.

## Output Format
For each relevant policy found, provide:

POLICY_EXCERPT_1:
  SOURCE: [document filename]
  SECTION: [section heading]
  CITATION: [formatted citation]
  CONTENT: [exact policy text — do NOT paraphrase]
  RELEVANCE: [why this applies to the current issue]

POLICY_EXCERPT_2:
  ... (repeat for all relevant excerpts)

SEARCH_QUERIES_USED: [list the queries you used]

If no relevant policy is found for any aspect of the issue, explicitly state:
NO_POLICY_FOUND_FOR: [aspect of the issue not covered by existing policies]
""",
        expected_output=(
            "A list of relevant policy excerpts with citations and source documents, "
            "plus a list of search queries used."
        ),
        agent=agent,
    )
