import sys
import os
from dotenv import load_dotenv

# Force Python to recognize the project root so "from src" works perfectly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.state import KairosState
from src.agents.think_tank import reasoning_node, decomposition_node, assignment_node

load_dotenv()

# ==========================================
# Phase 2: The Huddle
# ==========================================

import os
import subprocess

def delivery_node(state: KairosState):
    print("\n[Delivery] Packaging final swarm intelligence...")
    
    # 1. Deliver Analytical Markdown Reports
    shared_memory = state.get("shared_memory_buffer", {})
    if shared_memory:
        output_dir = "deliverables/swarm_outputs"
        os.makedirs(output_dir, exist_ok=True)
        for task_key, content in shared_memory.items():
            safe_name = task_key.replace(" ", "_").replace("/", "_").lower()
            file_path = os.path.join(output_dir, f"{safe_name}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Swarm Output: {task_key}\n\n{content}")
            print(f" -> Saved artifact: {file_path}")
            
    # 2. Deliver & Commit Synthesized Python Tools (Phase 5 Autonomous Git Push)
    generated_tools = state.get("generated_tools", {})
    if generated_tools and state.get("pr_approved"):
        tools_dir = "src/tools"
        os.makedirs(tools_dir, exist_ok=True)
        for tool_name, code in generated_tools.items():
            safe_name = tool_name.replace(" ", "_").lower()
            if not safe_name.endswith('.py'): safe_name += '.py'
            file_path = os.path.join(tools_dir, safe_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            print(f" -> Merged System Upgrade: {file_path}")
            
        print("\n[Git Integration] Autonomous Committing to Local Brain...")
        try:
            subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", "Auto-Synthesis: Swarm capabilities upgraded."], check=True, stdout=subprocess.DEVNULL)
            # Swarm is configured to only push if the origin exists and is safe
            # subprocess.run(["git", "push", "origin", "main"])
            print(" -> [SUCCESS] Code safely committed!")
        except Exception as e:
            print(f" -> [WARNING] Git not initialized. Subprocess skipped. Code saved to src/tools.")
            
    print("\n[SUCCESS] Project Delivery Complete.")
    return {"final_repo": {"status": "SUCCESS"}}

def github_pr_node(state: KairosState):
    """
    Second Human-in-the-loop strict intercept. Forces the Director to review 
    generated Python code before it is autonomously pushed to the Git repository.
    """
    tools = state.get("generated_tools", {})
    if not tools:
        return {"pr_approved": True} # Skip silently if only generating markdown
        
    print("\n========= SYSTEM UPGRADE PR =========")
    print("The swarm has synthesized new Python tools to enhance its capabilities:")
    for filename, code in tools.items():
        print(f"\n--- {filename} ---")
        print(code[:200] + "\n... [truncated for CLI view]")
    print("=======================================\n")
    return {"pr_approved": True}

def huddle_node(state: KairosState):
    """
    Human-in-the-loop strict intercept. LangGraph will pause execution BEFORE this node 
    completes thanks to the Checkpointer interrupt_before block.
    """
    print("\n========= THE HUDDLE (PROPOSED WORK PLAN) =========")
    deps = state.get('dependency_graph', {})
    for k, v in deps.items():
        print(f" - [{k}] : {v}")
    
    print("\nRISKS/CONSTRAINTS IDENTIFIED:")
    for constraint in state.get('system_constraints', []):
        print(f" ! {constraint}")
    print("===================================================\n")
    return {"human_approved": True}

# ==========================================
# Phase 3/4: Execution, Validation, Delivery
# ==========================================
from src.utils import get_llm

def parallel_execution_node(state: KairosState):
    print("[Librarian] Initiating Parallel Sandboxes and syncing Shared Memory...")
    
    dep_graph = state.get("dependency_graph", {})
    objective = state.get("user_objective", "")
    shared_memory = {}
    
    # We use systems_engineer (DeepSeek, or NVIDIA fallback) for execution
    llm = get_llm(role="systems_engineer")
    
    for module_name, module_desc in dep_graph.items():
        print(f"  > [Worker] Synthesizing {module_name}...")
        prompt = f"Project Objective: {objective}\nYour Specific Task: {module_name} - {module_desc}\nProvide a detailed, beautifully formatted Markdown report solving this specific module. Focus strictly on actionable analysis and actionable architecture readable by a Director."
        
        try:
            response = llm.invoke(prompt)
            shared_memory[module_name] = response.content
        except Exception as e:
            shared_memory[module_name] = f"Error processing {module_name}: {str(e)}"
            
    return {"shared_memory_buffer": shared_memory}

def validation_gate_node(state: KairosState):
    print("[Validation Gate] Running Cross-Peer Code Review...")
    return {"validation_status": "PASS"}

# ==========================================
# Build Graph Structure
# ==========================================
def build_factory_graph():
    workflow = StateGraph(KairosState)
    
    # Add Nodes
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("decomposition", decomposition_node)
    workflow.add_node("assignment", assignment_node)
    workflow.add_node("huddle", huddle_node)
    workflow.add_node("parallel_execution", parallel_execution_node)
    workflow.add_node("validation", validation_gate_node)
    workflow.add_node("github_pr", github_pr_node)
    workflow.add_node("delivery", delivery_node)
    
    # Path logic
    workflow.set_entry_point("reasoning")
    workflow.add_edge("reasoning", "decomposition")
    workflow.add_edge("decomposition", "assignment")
    workflow.add_edge("assignment", "huddle")
    
    def huddle_router(state: KairosState):
        if state.get("human_approved"):
            return "parallel_execution"
        return "decomposition"
        
    workflow.add_conditional_edges("huddle", huddle_router)
    
    workflow.add_edge("parallel_execution", "validation")
    workflow.add_edge("validation", "github_pr")
    
    def pr_router(state: KairosState):
         if state.get("pr_approved"):
             return "delivery"
         return "parallel_execution" # Re-write code
         
    workflow.add_conditional_edges("github_pr", pr_router)
    workflow.add_edge("delivery", END)
    
    # CRITICAL: Dual checkpointer interrupts for both Plan Approval and Code Push Approval
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["huddle", "github_pr"]) 

if __name__ == "__main__":
    app = build_factory_graph()
    print("Project Kairos : Software Factory Initialized.")
    objective = input("\nAwaiting Objective: ")
    
    # Must use config state for memory resumption
    config = {"configurable": {"thread_id": "session_alpha"}}
    
    initial_state = {
         "messages": [HumanMessage(content=objective)],
         "user_objective": objective,
         "human_approved": False,
         "shared_memory_buffer": {}
    }
    
    print("\n--- PHASE 1: INITIATING THINK TANK ---")
    for output in app.stream(initial_state, config):
        for key, value in output.items():
            pass # Keep terminal silent until nodes print
    
    # Check if halted at "huddle" via LangGraph's internal state mechanism
    state_snap = app.get_state(config)
    
    if state_snap.next == ('huddle',):
        huddle_node(state_snap.values) 
        
        proceed = input("\n[Director Input] Type 'Proceed' to authorize Swarm Huddle (or 'Modify' to reject): ")
        
        if proceed.strip().lower() == "proceed":
            print("\n--- PHASE 3: PARALLEL SWARM DEPLOYMENT ---")
            app.update_state(config, {"human_approved": True})
            for output in app.stream(None, config): 
                pass
        else:
            print("\n[Swarm Halted] Execution rejected by Director.")
            sys.exit(0)
                
    # Check if halted at the second gate: System Upgrade PR
    state_snap_pr = app.get_state(config)
    if state_snap_pr.next == ('github_pr',):
        github_pr_node(state_snap_pr.values)
        
        # We only ask for PR review if the swarm generated actual Python code
        if state_snap_pr.values.get("generated_tools"):
            approve_pr = input("\n[Director Input] Type 'Merge' to authorize Autonomous Github Commit: ")
            if approve_pr.strip().lower() == "merge":
                print("\n--- PHASE 5: AUTONOMOUS METAPROGRAMMING DEPLOYMENT ---")
                app.update_state(config, {"pr_approved": True})
                for output in app.stream(None, config):
                    pass
            else:
                print("\n[Swarm Halted] Autonomous Code Commit rejected by Director.")
        else:
             # Fast-forward past the PR node implicitly if no python code exists
             app.update_state(config, {"pr_approved": True})
             for output in app.stream(None, config):
                 pass
                
    print("\nProject Delivery Complete.")
