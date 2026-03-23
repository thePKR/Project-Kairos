import json
from typing import Dict, Any
from src.state import KairosState
from src.utils import get_llm

def reasoning_node(state: KairosState) -> Dict[str, Any]:
    """Reasoning Agent: Analyzes the initial objective to formulate edge cases and constraints."""
    print("[Think-Tank] Reasoner: Routing to core_reasoner (GPT-OSS logic)...")
    objective = state.get("user_objective", "")
    
    llm = get_llm(role="core_reasoner")
    prompt = f"""Analyze this software/system objective: '{objective}'. 
    Exhaustively list ALL critical technical constraints, risks, or edge cases necessary for success. Do not limit yourself; list as many as you encounter.
    Output ONLY a valid parseable python list of strings, e.g.: ['constraint 1', 'constraint 2', ...]. Do not wrap in markdown blocks."""
    
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
    """Assignment Agent: Maps the 8 equal capability profiles to graph nodes."""
    print("[Think-Tank] Assigner: Mapping swarm sub-agents...")
    
    dep_graph = state.get("dependency_graph", {})
    assignments = {}
    
    for i, key in enumerate(dep_graph.keys()):
        assignments[f"Worker_Profile_{i+1}"] = key
        
    return {"worker_assignments": assignments}
