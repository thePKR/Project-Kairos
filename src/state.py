from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class KairosState(TypedDict):
    """State schema entirely redesigned for the Software Factory pattern."""
    
    # Global Chat tracking
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 1. Activation Phase
    user_objective: str
    historical_context: str
    
    # 2. Think-Tank Phase
    system_constraints: List[str]
    dependency_graph: Dict[str, Any]  # The JSON-based graph
    worker_assignments: Dict[str, str] # e.g. {"Login UI": "Agent Profile 3"}
    interface_contract: str  # Shared API contract injected into every worker prompt
    
    # 3. The Huddle Phase
    huddle_plan_markdown: str
    human_approved: bool
    
    # 4. Parallel Execution Phase
    shared_memory_buffer: Dict[str, str] # High-speed Librarian view
    final_compiled_files: Dict[str, str] # Relative Path -> String Content
    
    # 4.5 Sandbox Self-Correction
    sandbox_error_log: str
    sandbox_retries: int
    
    # 5. Validation & Delivery (Phase 5 GitHub)
    validation_status: str
    generated_tools: Dict[str, str] # Filename -> Python Code 
    pr_approved: bool
    final_repo: Dict[str, str] # Filename -> Code mapping

    # 6. Scout / Tool-Maker (extended runtime fields)
    current_agent: str
    anomalies_detected: List[str]
    tool_requests: List[Dict[str, Any]]
