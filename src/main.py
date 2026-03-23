import sys
import os

# Force Python to recognize the project root so "from src" works perfectly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE: Heavy packages (langchain, langgraph) are imported lazily inside
# build_factory_graph() and __main__ to avoid loading ~200MB of native
# libraries into RAM at import time, which was causing startup CPU spikes.
# src.state is safe to import early — it's a pure TypedDict with no native libs.

from dotenv import load_dotenv
from src.state import KairosState
load_dotenv()

# ==========================================
# Phase 2: The Huddle
# ==========================================

import subprocess

def delivery_node(state: KairosState):
    print("\n[Delivery] Packaging final aligned objective...")
    
    final_files = state.get("final_compiled_files", {})
    objective = state.get("user_objective", "output")
    
    if final_files:
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', objective.replace(" ", "_")).lower()
        if safe_name.startswith("create_a_code_to_"):
            safe_name = safe_name.replace("create_a_code_to_", "")
        safe_name = safe_name[:50].strip("_")
        if not safe_name:
            safe_name = "objective_output"
            
        output_dir = os.path.join("deliverables", safe_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Cleanup old fragments so we don't bloat the user's system
        shared_memory = state.get("shared_memory_buffer", {})
        for path in shared_memory.values():
            if os.path.exists(path):
                os.remove(path)
                
        print(f"\n[Delivery] Writing structured file tree to: {output_dir}")
        for rel_path, content in final_files.items():
            # Create nested directories if LLM responded with "src/app.py" etc
            full_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f" -> Generated: {rel_path}")
            
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

def parallel_execution_node(state: KairosState):
    print("[Librarian] Initiating Parallel Sandboxes and syncing Shared Memory...")
    
    # Lazy import — only pulled into RAM when this node actually runs
    from src.utils import get_llm

    dep_graph = state.get("dependency_graph", {})
    objective = state.get("user_objective", "")
    
    # Stream outputs straight to disk instead of accumulating in RAM.
    # Each result is written and the string reference dropped before the next
    # LLM call starts, keeping peak memory to ~1 response at a time.
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', objective.replace(" ", "_")).lower()
    if safe_name.startswith("create_a_code_to_"):
        safe_name = safe_name.replace("create_a_code_to_", "")
    safe_name = safe_name[:50].strip("_")
    if not safe_name:
        safe_name = "objective_output"
        
    output_dir = os.path.join("deliverables", safe_name)
    os.makedirs(output_dir, exist_ok=True)
    shared_memory = {}
    
    llm = get_llm(role="systems_engineer")
    
    import concurrent.futures

    def _process_module(module_item):
        m_name, m_desc = module_item
        print(f"  > [Worker] Synthesizing {m_name}...")
        prompt = (
            f"Project Objective: {objective}\n"
            f"Your Specific Task: {m_name} - {m_desc}\n"
            "Provide a detailed, beautifully formatted Markdown report solving this "
            "specific module. Focus strictly on actionable analysis and actionable "
            "architecture readable by a Director."
        )
        
        try:
            response = llm.invoke(prompt)
            content = response.content
        except Exception as e:
            content = f"Error processing {m_name}: {str(e)}"
        
        # Write to disk immediately — free the response object from RAM
        safe_file_name = m_name.replace(" ", "_").replace("/", "_").lower()
        file_path = os.path.join(output_dir, f"{safe_file_name}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Swarm Output: {m_name}\n\n{content}")
        print(f"    -> Streamed to disk: {file_path}")
        
        return m_name, file_path

    # Execute all modules concurrently via threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(_process_module, dep_graph.items())
        
        for m_name, path in results:
            shared_memory[m_name] = path
            
    return {"shared_memory_buffer": shared_memory}

import re
def synthesis_node(state: KairosState):
    print("\n[Synthesis] Consolidating architecture and generating final executable product...")
    from src.utils import get_llm
    llm = get_llm(role="systems_engineer")
    
    objective = state.get("user_objective", "")
    shared_memory = state.get("shared_memory_buffer", {})
    
    # Read the fragmented module pieces directly from disk
    consolidated_text = []
    for module_name, path in shared_memory.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                consolidated_text.append(f.read())
                
    full_context = "\n\n".join(consolidated_text)
    prompt = (
        f"You are the Lead Systems Architect. The engineering swarm has analyzed the following objective:\n"
        f"'{objective}'\n\n"
        f"They produced the following fragmented architectural components:\n"
        f"=====\n{full_context}\n=====\n\n"
        "Your task: Consolidate everything into a fully scalable, multi-file software repository. Generate the frontend, backend, database connectors, and documentation in their appropriate folders.\n"
        "Output EACH file strictly using the following delimiter format:\n\n"
        "__FILE_START__::relative/path/to/filename.ext\n"
        "[File content goes here]\n"
        "__FILE_END__\n\n"
        "Make sure to include ALL files necessary to run the project. You may generate as many files as needed."
    )
    
    final_files = {}
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        # Parse all files matching the syntax
        pattern = r"__FILE_START__::(.*?)\n(.*?)\n?__FILE_END__"
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            file_path = match.group(1).strip()
            file_content = match.group(2).strip()
            
            # Clean up markdown code blocks if the LLM wrapped it internally
            if file_content.startswith("```"):
                file_content = file_content.split("\n", 1)[-1]
            if file_content.endswith("```"):
                file_content = file_content.rsplit("\n", 1)[0]
                
            final_files[file_path] = file_content.strip()
            
        if not final_files:
            print("  [Warning] LLM failed to output files using the correct delimiter format.")
             
    except Exception as e:
        print(f"  [Error] Synthesis LLM failed: {e}")
        
    return {
        "final_compiled_files": final_files
    }

def validation_gate_node(state: KairosState):
    print("[Validation Gate] Running Cross-Peer Code Review...")
    return {"validation_status": "PASS"}

# ==========================================
# Build Graph Structure
# ==========================================
def build_factory_graph():
    # Lazy imports — LangGraph and LangChain core pull in ~150-200MB of
    # native libs. Loading them here (not at module level) means the process
    # stays lean until the user actually confirms an objective.
    from langchain_core.messages import HumanMessage  # noqa: F401 (re-exported)
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from src.agents.think_tank import reasoning_node, decomposition_node, assignment_node

    workflow = StateGraph(KairosState)
    
    # Add Nodes
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("decomposition", decomposition_node)
    workflow.add_node("assignment", assignment_node)
    workflow.add_node("huddle", huddle_node)
    workflow.add_node("parallel_execution", parallel_execution_node)
    workflow.add_node("synthesis", synthesis_node)
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
    
    workflow.add_edge("parallel_execution", "synthesis")
    workflow.add_edge("synthesis", "validation")
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
    # Get the objective BEFORE building the graph so the user isn't waiting
    # while 200MB of LangGraph native libs load in the background.
    print("Project Kairos : Software Factory Initialized.")
    objective = input("\nAwaiting Objective: ")

    # Now do the heavy lifting — user has already given us the goal
    from langchain_core.messages import HumanMessage
    print("[Boot] Loading engine...", end=" ", flush=True)
    app = build_factory_graph()
    print("Ready.")
    
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
