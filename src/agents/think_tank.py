import json
from typing import Dict, Any
from src.state import KairosState
from src.utils import get_llm

def reasoning_node(state: KairosState) -> Dict[str, Any]:
    """Reasoning Agent: Analyzes the initial objective to formulate edge cases and constraints."""
    print("[Think-Tank] Reasoner: Routing to core_reasoner (GPT-OSS logic)...")
    objective = state.get("user_objective", "")
    historical_context = state.get("historical_context", "")
    
    llm = get_llm(role="core_reasoner")
    prompt = f"Analyze this software/system objective: '{objective}'.\n"
    
    if historical_context:
        prompt += f"\nYou have Long-Term Graph Memory of past objectives. Consider them strictly as context to avoid duplicating logic or repeating architectural mistakes:\n{historical_context}\n"
        
    prompt += "\nExhaustively list ALL critical technical constraints, risks, or edge cases necessary for success. Do not limit yourself; list as many as you encounter.\n    Output ONLY a valid parseable python list of strings, e.g.: ['constraint 1', 'constraint 2', ...]. Do not wrap in markdown blocks."
    
    try:
        response = llm.invoke(prompt)
        content_str = str(response.content)
        content = content_str.replace('```python', '').replace('```', '').strip()
        constraints = eval(content) if '[' in content else [content]
    except Exception as e:
        print(f"  [Error] Reasoner LLM failed: {e}")
        constraints = ["Strictly evaluate edge cases manually"]
        
    return {"system_constraints": constraints}

def decomposition_node(state: KairosState) -> Dict[str, Any]:
    """Decomposition Agent: Translates the objective and constraints into a Dependency Graph."""
    print("[Think-Tank] Decomposer: Routing to systems_engineer (DeepSeek logic)...")
    objective = state.get("user_objective", "")
    constraints = state.get("system_constraints", [])
    
    llm = get_llm(role="systems_engineer")
    prompt = f"""Break down this objective into a comprehensive array of modular software tasks: '{objective}'. 
    Keep these constraints in mind: {constraints}. Break it down into as many distinct tasks as necessary to perfectly fulfill the objective.
    IMPORTANT: Keep the number of modules between 5 and 10. Do NOT create modules for generic concerns like 'Logger', 'Authenticator', 'CI_CD', 'Monitor', 'Backup_Recovery' — focus ONLY on the core product features.
    Output ONLY a raw valid JSON object where keys correspond to module names and values are short descriptions. Do not wrap in markdown blocks. Example: {{"Data_Ingestion": "Fetch prices"}}"""
    
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
    
    contract_prompt = f"""You are a Systems Architect. Given this objective: '{objective}'
And these modules:
{modules_list}

Generate a SHARED INTERFACE CONTRACT that every module developer MUST follow.
For each module, specify:
1. The filename (e.g., scraper/web_scraper.py)
2. The function signatures with exact parameter names and return types
3. Required imports (use ONLY modern, current package APIs)

CRITICAL RULES:
- Every Python file MUST start with all required imports (os, json, etc.)
- Use the modern OpenAI v1+ API: `from openai import OpenAI` then `client = OpenAI(...)` then `client.chat.completions.create()`
- NEVER use deprecated APIs like `openai.Completion.create()`
- For streamlit-agraph, use: `from streamlit_agraph import agraph, Node, Edge, Config`
- For Neo4j, use: `from neo4j import GraphDatabase`
- For env vars, use: `import os` then `os.environ.get("KEY", "default")`
- All functions must include `import os` if they reference `os.environ`
- requirements.txt must NOT have version pins (just package names)
- Do NOT include stdlib packages in requirements.txt (e.g., no concurrent.futures)

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
