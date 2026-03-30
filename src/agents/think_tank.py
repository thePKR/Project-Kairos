import json
from typing import Dict, Any
from src.state import KairosState  # type: ignore
from src.utils import get_llm  # type: ignore

def reasoning_node(state: KairosState) -> Dict[str, Any]:
    """Reasoning Agent: Analyzes the initial objective to formulate edge cases and constraints."""
    print("[Think-Tank] Reasoner: Routing to core_reasoner (GPT-OSS logic)...")
    objective = state.get("user_objective", "")
    historical_context = state.get("historical_context", "")
    deliverables_context = state.get("deliverables_context", "")
    
    llm = get_llm(role="core_reasoner")
    prompt = f"Analyze this software/system objective: '{objective}'.\n"
    
    # RAG: Inject criteria that must not be violated
    rag_criteria = state.get("rag_criteria", [])
    if rag_criteria:
        prompt += (
            "\n=== CRITERIA THAT MUST NOT BE VIOLATED (FROM PRIOR COMMANDS) ===\n"
            + "\n".join(f"• {c}" for c in rag_criteria)
            + "\n=== END CRITERIA ===\n\n"
        )
    rag_cross = state.get("rag_cross_session_context", "")
    if rag_cross:
        prompt += (
            "\n=== RELEVANT CONTEXT FROM PAST SESSIONS ===\n"
            + rag_cross
            + "\n=== END PAST CONTEXT ===\n\n"
        )
    
    if historical_context:
        prompt += f"\nYou have Long-Term Graph Memory of past objectives. Consider them strictly as context to avoid duplicating logic or repeating architectural mistakes:\n{historical_context}\n"
        
    if deliverables_context:
        prompt += f"\nThe user has provided an existing codebase (deliverables). Consider these files as the foundation to analyze and modify:\n{deliverables_context}\n"
        
    prompt += (
        "\n1. Explicitly determine the absolute BEST programming language and technology framework stack "
        "(e.g., 'Rust/Actix', 'Go/Gin', 'Node.js/Express', 'Python/FastAPI', 'HTML/JS/CSS') for this specific objective. Do not default to Python unless it is truly the best fit.\n"
        "2. Exhaustively list ALL critical technical constraints, risks, or edge cases necessary for success.\n"
        "Output ONLY a raw, valid JSON object containing exactly two keys: 'tech_stack' (string) and 'constraints' (list of strings).\n"
        "Do not wrap the output in markdown blocks. Example: {\"tech_stack\": \"Go/Goji\", \"constraints\": [\"Risk A\", \"Context B\"]}"
    )
    
    try:
        response = llm.invoke(prompt)
        content_str = str(response.content)
        content = content_str.replace('```json', '').replace('```', '').strip()
        data = json.loads(content)
        tech_stack = data.get("tech_stack", "Python")
        constraints = data.get("constraints", [])
    except Exception as e:
        print(f"  [Error] Reasoner LLM failed: {e}")
        tech_stack = "Python (Default Fallback)"
        constraints = ["Strictly evaluate edge cases manually"]
        
    print(f"  -> Selected Tech Stack: {tech_stack}")
    return {"tech_stack": tech_stack, "system_constraints": constraints}

def decomposition_node(state: KairosState) -> Dict[str, Any]:
    """Decomposition Agent: Translates the objective and constraints into a Dependency Graph."""
    print("[Think-Tank] Decomposer: Routing to systems_engineer (DeepSeek logic)...")
    objective = state.get("user_objective", "")
    constraints = state.get("system_constraints", [])
    tech_stack = state.get("tech_stack", "Python")
    deliverables_context = state.get("deliverables_context", "")
    
    llm = get_llm(role="systems_engineer")
    prompt = f"""Break down this objective into a comprehensive array of modular software tasks: '{objective}'. 
    You must strictly build the architecture using this Tech Stack: {tech_stack}.
    Keep these constraints in mind: {constraints}. Break it down into as many distinct tasks as necessary to perfectly fulfill the objective.
    IMPORTANT: Keep the number of modules between 5 and 10. Do NOT create modules for generic concerns like 'Logger', 'Authenticator', 'CI_CD', 'Monitor', 'Backup_Recovery' — focus ONLY on the core product features.
    If building a generic website frontend (HTML/JS), output tasks like 'index.html structure', 'styles.css layout', 'app.js logic', instead of Python-centric concepts."""
    
    # RAG: Inject criteria that must not be violated
    rag_criteria = state.get("rag_criteria", [])
    if rag_criteria:
        prompt += (
            "\n\n=== CRITERIA THAT MUST NOT BE VIOLATED (FROM PRIOR COMMANDS) ===\n"
            + "\n".join(f"• {c}" for c in rag_criteria)
            + "\n=== END CRITERIA ===\n"
        )
    
    if deliverables_context:
        prompt += f"\n\nIMPORTANT: The user has provided an existing codebase to work on:\n{deliverables_context}\n\nYour tasks MUST involve modifying, refactoring, or extending these existing files where appropriate, rather than re-building everything from scratch."
        
    prompt += """\n\nOutput ONLY a raw valid JSON object where keys correspond to module names and values are short descriptions. Do not wrap in markdown blocks. Example: {{"Data_Ingestion": "Fetch prices"}}"""
    
    try:
        response = llm.invoke(prompt)
        content_str = str(response.content)
        content = content_str.replace('```json', '').replace('```', '').strip()
        dep_graph = json.loads(content)
    except Exception as e:
         print(f"  [Error] Decomposer LLM failed: {e}")
         dep_graph = {"Task_1": "Analyze market momentum", "Task_2": "Build risk management protocol"}

    return {"dependency_graph": dep_graph}


def assignment_node(state: KairosState) -> Dict[str, Any]:
    """
    Assignment Agent: Maps worker profiles to graph nodes AND generates
    a shared Interface Contract so all workers produce compatible code.
    """
    print("[Think-Tank] Assigner: Mapping swarm sub-agents and generating Interface Contract...")
    
    dep_graph = state.get("dependency_graph", {})
    objective = state.get("user_objective", "")
    assignments = {}
    
    for i, key in enumerate(dep_graph.keys()):
        assignments[f"Worker_Profile_{i+1}"] = key
    
    # Generate the Interface Contract via LLM
    llm = get_llm(role="systems_engineer")
    modules_list = "\n".join([f"- {k}: {v}" for k, v in dep_graph.items()])
    deliverables_context = state.get("deliverables_context", "")
    
    contract_prompt = f"""You are a Systems Architect. Given this objective: '{objective}'
And these modules:
{modules_list}
"""
    # RAG: Inject criteria that must not be violated
    rag_criteria = state.get("rag_criteria", [])
    if rag_criteria:
        contract_prompt += (
            "\n=== CRITERIA THAT MUST NOT BE VIOLATED (FROM PRIOR COMMANDS) ===\n"
            + "\n".join(f"• {c}" for c in rag_criteria)
            + "\n=== END CRITERIA ===\n\n"
        )
    if deliverables_context:
        contract_prompt += f"And this existing codebase:\n{deliverables_context}\n\n"
        
    tech_stack = state.get("tech_stack", "Python")
    contract_prompt += f"""Generate a SHARED INTERFACE CONTRACT that every module developer MUST follow.
This project MUST be built using strictly this Tech Stack: {tech_stack}.

For each module, specify:
1. The exact filename with idiomatic extension (e.g., scraper.go, index.html, main.rs, app.py)
2. The function signatures, structs, or component layouts with exact parameter names and types appropriate for the language.
3. Required imports, dependencies, or standard library includes.

CRITICAL RULES:
- If the stack is Python, mandate modern APIs and `os.environ` patterns.
- If the stack is web frontend (HTML/JS/CSS), prohibit Streamlit/Python backend emulation. Use pure frontend standards, CDN links, and modern Javascript ES6.
- If the stack is Go, Rust, C++, Java, or Node, explicitly define package scopes, export naming constraints, and build tool requirements (`go.mod`, `Cargo.toml`, `package.json`, etc.).
- The dependencies manifest must match the language (e.g., do not generate requirements.txt for a Node app).

Output ONLY a clean text specification. No markdown blocks."""

    try:
        response = llm.invoke(contract_prompt)
        interface_contract = str(response.content).strip()
        print("  -> Interface Contract generated successfully.")
    except Exception as e:
        print(f"  [Error] Contract generation failed: {e}")
        interface_contract = "Ensure all files have correct imports. Use modern APIs only."
        
    return {
        "worker_assignments": assignments,
        "interface_contract": interface_contract
    }
