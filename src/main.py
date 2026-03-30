import sys
import os
import subprocess

# --- HOTFIX: Bypass Windows WMI Hang ---
# Some Windows environments have a broken WMI service that causes platform.system() to hang infinitely.
import platform
platform.system = lambda: "Windows"
if hasattr(platform, '_wmi_query'):
    platform._wmi_query = lambda *args, **kwargs: ("10", "1", "1", 0, 0)
# ---------------------------------------

# Auto-install missing requirements if running directly
try:
    import dotenv  # type: ignore
    import langgraph  # type: ignore
    import langchain_core  # type: ignore
except ImportError:
    print("\n[Kairos] ⚠️ Missing dependencies detected.")
    print("[Kairos] ⏳ DO NOT CANCEL. Automatically installing from requirements.txt. This may take a minute...")
    req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
    if os.path.exists(req_path):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path, "-q"])
            print("[Kairos] ✅ Dependencies installed successfully. Restarting...\n")
            sys.exit(subprocess.call([sys.executable] + sys.argv))
        except Exception as e:
            print(f"[Kairos] Failed to install dependencies: {e}")
            sys.exit(1)
    else:
        print("[Kairos] requirements.txt not found. Cannot auto-install dependencies.\n")

# Force Python to recognize the project root so "from src" works perfectly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE: Heavy packages (langchain, langgraph) are imported lazily inside
# build_factory_graph() and __main__ to avoid loading ~200MB of native
# libraries into RAM at import time, which was causing startup CPU spikes.
# src.state is safe to import early — it's a pure TypedDict with no native libs.

from dotenv import load_dotenv  # type: ignore
from src.state import KairosState  # type: ignore
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
        safe_name = str(safe_name)[:50].strip("_")  # type: ignore
        if not safe_name:
            safe_name = "objective_output"
            
        output_dir = os.path.join("deliverables", safe_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Cleanup old fragments so we don't bloat the user's system
        shared_memory = state.get("shared_memory_buffer", {})
        for path in shared_memory.values():
            if os.path.exists(str(path)):
                os.remove(str(path))  # type: ignore
                
        print(f"\n[Delivery] Writing structured file tree to: {output_dir}")
        for rel_path, content in final_files.items():
            # Create nested directories if LLM responded with "src/app.py" etc
            full_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f" -> Generated: {rel_path}")
            
        # Archive the final objective to Neo4j Long-Term Memory
        dep_graph = state.get("dependency_graph", {})
        if dep_graph and final_files:
            try:
                from src.memory.graph_manager import KairosGraphManager  # type: ignore
                manager = KairosGraphManager()
                manager.archive_project(objective, dep_graph, final_files)
            except Exception as e:
                print(f"  [Memory Error] Could not archive to graph: {e}")
            
        # RAG: Commit this command to the session log
        try:
            from src.rag.context_engine import KairosContextEngine  # type: ignore
            from src.rag.constraint_decoder import KairosConstraintDecoder  # type: ignore
            rag_engine = KairosContextEngine()
            session_id = state.get("rag_session_id", "")
            if session_id:
                rag_engine.resume_session(session_id)
                decoder = KairosConstraintDecoder()
                tech_stack = state.get("tech_stack", "")
                new_criteria = decoder.extract_criteria(objective, tech_stack, dep_graph, final_files)
                modules_list = list(final_files.keys()) if final_files else []
                outcome = state.get("validation_status", "COMPLETED")
                rag_engine.commit_command(
                    objective=objective,
                    tech_stack=tech_stack,
                    modules=modules_list,
                    outcome=outcome,
                    criteria=new_criteria
                )
        except Exception as e:
            print(f"  [RAG] Warning: Could not commit to session log: {e}")
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
    from src.utils import get_llm  # type: ignore

    dep_graph = state.get("dependency_graph", {})
    objective = state.get("user_objective", "")
    
    # Stream outputs straight to disk instead of accumulating in RAM.
    # Each result is written and the string reference dropped before the next
    # LLM call starts, keeping peak memory to ~1 response at a time.
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', objective.replace(" ", "_")).lower()
    if safe_name.startswith("create_a_code_to_"):
        safe_name = safe_name.replace("create_a_code_to_", "")
    safe_name = str(safe_name)[:50].strip("_")  # type: ignore
    if not safe_name:
        safe_name = "objective_output"
        
    output_dir = os.path.join("deliverables", safe_name)
    os.makedirs(output_dir, exist_ok=True)
    shared_memory = {}
    
    llm = get_llm(role="systems_engineer")
    tech_stack = state.get("tech_stack", "Python")
    import concurrent.futures

    def _process_module(module_item):
        m_name, m_desc = module_item
        print(f"  > [Worker] Synthesizing {m_name}...")
        
        # Inject the shared Interface Contract so all workers produce compatible code
        contract = state.get("interface_contract", "")
        deliverables_context = state.get("deliverables_context", "")
        prompt = (
            f"Project Objective: {objective}\n"
            f"Your Specific Task: {m_name} - {m_desc}\n\n"
        )
        if contract:
            prompt += (
                f"=== SHARED INTERFACE CONTRACT (ALL WORKERS MUST FOLLOW) ===\n"
                f"{contract}\n"
                f"=== END CONTRACT ===\n\n"
            )
        if deliverables_context:
            prompt += (
                f"=== EXISTING CODEBASE (DELIVERABLES) ===\n"
                f"{deliverables_context}\n"
                f"=== END EXISTING CODEBASE ===\n"
                f"Your task is to modify or extend these files where appropriate, reducing redundant work.\n\n"
            )
        prompt += (
            f"Provide a detailed, beautifully formatted Markdown report solving this "
            f"specific module. Include CONCRETE code using the designated Tech Stack ({tech_stack}) "
            f"that follows the Interface Contract exactly. "
            f"Every code block must have correct syntax and imports. Focus strictly on actionable "
            f"architecture readable by a Director.\n\n"
            f"CRITICAL RULE: You MUST output ALL code strictly using the following delimiter format:\n"
            "__FILE_START__::relative/path/to/filename.ext\n"
            "[File content goes here]\n"
            "__FILE_END__\n"
        )
        
        import time
        start_time = time.time()
        try:
            response = llm.invoke(prompt)
            content = response.content
        except Exception as e:
            content = f"Error processing {m_name}: {str(e)}"
        duration = time.time() - start_time
        
        # Write to disk immediately — free the response object from RAM
        safe_file_name = m_name.replace(" ", "_").replace("/", "_").lower()
        file_path = os.path.join(output_dir, f"{safe_file_name}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Swarm Output: {m_name}\n\n{content}")
        print(f"    -> [completed in {duration:.1f}s] Streamed to disk: {file_path}")
        
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
    from src.utils import get_llm  # type: ignore
    llm = get_llm(role="systems_engineer")
    
    objective = state.get("user_objective", "")
    shared_memory = state.get("shared_memory_buffer", {})
    
    # Read the fragmented module pieces directly from disk
    consolidated_text = []
    for module_name, path in shared_memory.items():
        if os.path.exists(str(path)):
            with open(str(path), "r", encoding="utf-8") as f:
                consolidated_text.append(f.read())
                
    full_context = "\n\n".join(consolidated_text)
    
    # Load known packages for grounding
    import json as _json
    known_packages = ""
    pkg_path = os.path.join(os.path.dirname(__file__), "resources", "known_packages.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r") as pf:
            pkg_data = _json.load(pf)
            known_packages = ", ".join(pkg_data.keys())
    
    # Inject the interface contract into synthesis
    contract = state.get("interface_contract", "")
    tech_stack = state.get("tech_stack", "Python")
    
    final_files = {}
    
    # Self-correction: if the sandbox found errors, inject them
    sandbox_error = state.get("sandbox_error_log", "")
    if sandbox_error:
        retries = state.get("sandbox_retries", 0)
        print(f"  [Sandbox Patching] Automatically patching Sandbox errors (Retry {retries})...")
        prompt = (
            f"You are the Lead Systems Architect. The engineering swarm built this architecture:\n"
            f"'{objective}'\n\n"
            f"Here is the context:\n=====\n{str(full_context)[:20000]}\n=====\n\n"
            f"⚠️ CRITICAL: Your previous code execution FAILED testing. The subprocess returned this error:\n"
            f"```\n{sandbox_error[:1500]}\n```\n"
            f"You MUST fix the bug. Return ONLY the files that need to be fixed, strictly using this exact format:\n\n"
            f"__FILE_START__::relative/path/to/filename.ext\n"
            f"__FILE_START__::relative/path/to/filename.ext\n"
            f"# (Write the FULL fixed code for this file here. Do NOT output placeholder text!)\n"
            f"__FILE_END__\n"
        )
        import time
        start = time.time()
        try:
            res = llm.invoke(prompt)
            content = res.content
            dur = time.time() - start
            print(f"  [Sandbox Patching] Correction generated in {dur:.1f}s.")
        except Exception as e:
            print(f"  [Error] Correction LLM failed: {e}")
            content = ""
            
        # Re-populate final_files with the previous good pass so we can just overwrite the patched ones below
        prev_files = state.get("final_compiled_files", {})
        if prev_files:
            final_files.update(prev_files)
    else:
        # PURE HAPPY PATH FAST EXTRACTION!
        print("  [Pass 1] Instant Regex File Extraction...")
        content = full_context
        
    # Parse all files matching the syntax (applies to both Extraction and Sandbox Patching)
    pattern = r"__FILE_START__::(.*?)\n(.*?)\n?__FILE_END__"
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        file_path = match.group(1).strip()
        file_content = match.group(2).strip()
        
        # Clean up markdown code blocks if they are present
        if file_content.startswith("```"):
            file_content = file_content.split("\n", 1)[-1]
        if file_content.endswith("```"):
            file_content = file_content.rsplit("\n", 1)[0]
            
        final_files[file_path] = file_content.strip()
        
    if not final_files:
        print("  [Warning] Output failed to resolve files using the correct delimiter format.")
        
    # Guarantee a README exists with setup instructions if the fast-extraction missed one
    if "README.md" not in final_files and "readme.md" not in final_files:
        print("  [Documentation] Generating setup instructions...")
        readme_prompt = (
             f"You are the Lead Systems Architect. The swarm just generated a {tech_stack} project "
             f"with these files: {list(final_files.keys())}.\n"
             f"Generate a professional, concise README.md with step-by-step instructions on how the user can "
             f"install any dependencies and start/run this exact architecture on their local machine.\n"
             f"Do NOT include placeholders, output ONLY the raw markdown content for the README.md file."
        )
        try:
            readme_res = llm.invoke(readme_prompt)
            final_files["README.md"] = str(readme_res.content).replace('```markdown', '').replace('```', '').strip()
        except Exception:
            pass
            
    return {
        "final_compiled_files": final_files
    }

def validation_gate_node(state: KairosState):
    """Cross-file AST validation: checks imports, detects missing os/json, and verifies structure."""
    print("[Validation Gate] Running Cross-File AST Analysis...")
    import ast
    
    final_files = state.get("final_compiled_files", {})
    issues = []
    
    for filepath, content in final_files.items():
        if not filepath.endswith(".py"):
            continue
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append(f"SyntaxError in {filepath}: {e}")
            continue
        
        # Collect all imported names
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(str(node.module).split(".")[0])  # type: ignore
        
        # Check for common missing imports
        source = str(content)
        if "os.environ" in source or "os.path" in source or "os.makedirs" in source:
            if "os" not in imported_names:
                issues.append(f"{filepath}: uses 'os' but never imports it")
        if "json.loads" in source or "json.dumps" in source:
            if "json" not in imported_names:
                issues.append(f"{filepath}: uses 'json' but never imports it")
        if "re." in source:
            if "re" not in imported_names:
                issues.append(f"{filepath}: uses 're' but never imports it")
    
    if issues:
        print(f"  -> Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"     ⚠️ {issue}")
    else:
        print("  -> ✅ All files passed AST validation.")
    
    return {"validation_status": "PASS" if not issues else f"ISSUES: {'; '.join(issues)}"}

def sandbox_node(state: KairosState):
    """Executes generated code in an isolated subprocess and captures errors."""
    from src.sandbox.executor import run_in_sandbox, MAX_RETRIES  # type: ignore
    
    final_files = state.get("final_compiled_files", {})
    retries = state.get("sandbox_retries", 0)
    
    # Skip sandbox if no Python files exist (e.g., pure documentation)
    has_python = any(p.endswith(".py") for p in final_files.keys())
    if not has_python:
        print("[Sandbox] No Python files detected. Skipping execution test.")
        return {"sandbox_error_log": "", "sandbox_retries": retries}
    
    print(f"\n[Sandbox] Attempt {retries + 1}/{MAX_RETRIES} — Executing generated code...")
    result = run_in_sandbox(final_files)
    
    if result["success"]:
        print(f" -> ✅ Code executed successfully. Entry: {result['entry_point']}")
        if result["stdout"]:
            print(f"    stdout: {result['stdout'][:300]}")
        return {"sandbox_error_log": "", "sandbox_retries": retries}
    else:
        error_msg = result["stderr"]
        print(f" -> ❌ Execution FAILED (attempt {retries + 1}/{MAX_RETRIES})")
        print(f"    stderr: {error_msg[:500]}")
        return {"sandbox_error_log": error_msg, "sandbox_retries": retries + 1}

def memory_retrieval_node(state: KairosState):
    print("\n[Memory] Connecting to Neo4j to retrieve past architectures...")
    from src.memory.graph_manager import KairosGraphManager  # type: ignore
    manager = KairosGraphManager()
    objective = state.get("user_objective", "")
    historical = manager.retrieve_context(objective)
    
    if historical:
        print(" -> Found relevant past objectives. Ingesting context.")
    else:
        print(" -> No relevant historical context found. Starting fresh.")
        
    return {"historical_context": historical}

# ==========================================
# RAG Context Nodes (Prakhar Rai — Original Design)
# ==========================================

def rag_context_node(state: KairosState):
    """Reads the current session log + cross-reads all other sessions for relevant criteria."""
    print("\n[RAG] Scanning session context...")
    from src.rag.context_engine import KairosContextEngine  # type: ignore
    from src.rag.constraint_decoder import KairosConstraintDecoder  # type: ignore
    
    session_id = state.get("rag_session_id", "")
    objective = state.get("user_objective", "")
    
    engine = KairosContextEngine()
    if session_id:
        engine.resume_session(session_id)
    
    # 1. Read criteria from current session
    current_criteria = engine.load_current_session_criteria()
    
    # 2. Cross-read all other sessions for relevant criteria
    cross_session = engine.cross_read(objective)
    
    # 3. Detect relevance
    decoder = KairosConstraintDecoder()
    analysis = decoder.detect_relevant_criteria(objective, current_criteria, cross_session)
    
    # Build cross-session context string for prompt injection
    cross_ctx = ""
    if analysis["cross_session"]:
        parts = []
        for sid, data in analysis["cross_session"].items():
            parts.append(
                f"Session '{sid}' (objective: {data['first_objective']}):\n"
                + "\n".join(f"  • {c}" for c in data["criteria"])
            )
        cross_ctx = "\n\n".join(parts)
    
    cmd_num = engine.command_count + 1
    
    if current_criteria:
        print(f" -> Found {len(current_criteria)} criteria from this session.")
    if cross_session:
        print(f" -> Found relevant context from {len(cross_session)} past session(s).")
    if not current_criteria and not cross_session:
        print(" -> No prior criteria. Starting fresh.")
    
    return {
        "rag_criteria": current_criteria,
        "rag_command_number": cmd_num,
        "rag_cross_session_context": cross_ctx
    }

def rag_negotiation_node(state: KairosState):
    """
    Interactive checkpoint: if prior criteria are detected, present them
    to the user and ask whether to Proceed, Modify, or Ignore.
    LangGraph will interrupt_before this node.
    """
    criteria = state.get("rag_criteria", [])
    cross_ctx = state.get("rag_cross_session_context", "")
    
    if not criteria and not cross_ctx:
        # No prior criteria — skip negotiation silently
        return {"rag_criteria": []}
    
    print("\n═══════════════════════════════════════════════════════")
    print("[RAG] Prior criteria detected that may guide this command:")
    print("═══════════════════════════════════════════════════════")
    
    if criteria:
        print("\nFrom THIS session:")
        for i, c in enumerate(criteria, 1):
            print(f"  {i}. {c}")
    
    if cross_ctx:
        print(f"\nFrom PAST sessions:")
        print(f"  {cross_ctx}")
    
    print("\n[Director Input] Options:")
    print("  1. proceed  — accept all criteria as binding")
    print("  2. modify   — edit specific criteria before proceeding")
    print("  3. ignore   — discard all prior criteria for this command")
    
    choice = input("\nYour choice (proceed/modify/ignore): ").strip().lower()
    
    if choice == "ignore" or choice == "3":
        print("[RAG] All prior criteria discarded for this command.")
        return {"rag_criteria": [], "rag_cross_session_context": ""}
    
    elif choice == "modify" or choice == "2":
        if criteria:
            print("\n[RAG] Current session criteria:")
            for i, c in enumerate(criteria, 1):
                print(f"  {i}. {c}")
            print("\nType the number(s) to REMOVE (comma-separated), or press Enter to keep all:")
            to_remove = input("> ").strip()
            if to_remove:
                try:
                    indices = [int(x.strip()) - 1 for x in to_remove.split(",")]
                    criteria = [c for i, c in enumerate(criteria) if i not in indices]
                    print(f"[RAG] Kept {len(criteria)} criteria after modification.")
                except ValueError:
                    print("[RAG] Invalid input. Keeping all criteria.")
            
            print("\nAdd new criteria? (pipe-separated, or press Enter to skip):")
            new_criteria = input("> ").strip()
            if new_criteria:
                additions = [c.strip() for c in new_criteria.split("|") if c.strip()]
                criteria.extend(additions)
                print(f"[RAG] Added {len(additions)} new criteria.")
        
        return {"rag_criteria": criteria}
    
    else:  # proceed (default)
        print("[RAG] All criteria accepted as binding.")
        return {"rag_criteria": criteria}

# ==========================================
# Build Graph Structure
# ==========================================
def build_factory_graph():
    # Lazy imports — LangGraph and LangChain core pull in ~150-200MB of
    # native libs. Loading them here (not at module level) means the process
    # stays lean until the user actually confirms an objective.
    from langchain_core.messages import HumanMessage  # type: ignore
    from langgraph.graph import StateGraph, END  # type: ignore
    from langgraph.checkpoint.memory import MemorySaver  # type: ignore
    from src.agents.think_tank import reasoning_node, decomposition_node, assignment_node  # type: ignore

    workflow = StateGraph(KairosState)
    
    # Add Nodes — RAG context comes first (Prakhar Rai — Original Design)
    workflow.add_node("rag_context", rag_context_node)
    workflow.add_node("rag_negotiation", rag_negotiation_node)
    workflow.add_node("memory_retrieval", memory_retrieval_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("decomposition", decomposition_node)
    workflow.add_node("assignment", assignment_node)
    workflow.add_node("huddle", huddle_node)
    workflow.add_node("parallel_execution", parallel_execution_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("sandbox", sandbox_node)
    workflow.add_node("validation", validation_gate_node)
    workflow.add_node("github_pr", github_pr_node)
    workflow.add_node("delivery", delivery_node)
    
    # Path logic — RAG is the new entry point
    workflow.set_entry_point("rag_context")
    workflow.add_edge("rag_context", "rag_negotiation")
    workflow.add_edge("rag_negotiation", "memory_retrieval")
    workflow.add_edge("memory_retrieval", "reasoning")
    workflow.add_edge("reasoning", "decomposition")
    workflow.add_edge("decomposition", "assignment")
    workflow.add_edge("assignment", "huddle")
    
    def huddle_router(state: KairosState):
        if state.get("human_approved"):
            return "parallel_execution"
        return "decomposition"
        
    workflow.add_conditional_edges("huddle", huddle_router)
    
    workflow.add_edge("parallel_execution", "synthesis")
    workflow.add_edge("synthesis", "sandbox")
    
    def sandbox_router(state: KairosState):
        from src.sandbox.executor import MAX_RETRIES  # type: ignore
        error_log = state.get("sandbox_error_log", "")
        retries = state.get("sandbox_retries", 0)
        if error_log and retries < MAX_RETRIES:
            print(f"[Sandbox Router] Re-routing to synthesis for self-correction (retry {retries}/{MAX_RETRIES})...")
            return "synthesis"
        return "validation"
    
    workflow.add_conditional_edges("sandbox", sandbox_router)
    workflow.add_edge("validation", "github_pr")
    
    def pr_router(state: KairosState):
         if state.get("pr_approved"):
             return "delivery"
         return "parallel_execution" # Re-write code
         
    workflow.add_conditional_edges("github_pr", pr_router)
    workflow.add_edge("delivery", END)
    
    # CRITICAL: Triple checkpointer interrupts — RAG Negotiation, Plan Approval, Code Push Approval
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["rag_negotiation", "huddle", "github_pr"]) 

def main():
    from src.rag.context_engine import KairosContextEngine  # type: ignore

    # ──────────────────────────────────────────
    # Human-Friendly Interactive Menu
    # ──────────────────────────────────────────

    print("")
    print("╔══════════════════════════════════════════════════════╗")
    print("║         PROJECT KAIROS — Software Factory           ║")
    print("║           Autonomous AI Build System                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    print("")

    # Handle --reset-rag CLI flag
    if "--reset-rag" in sys.argv:
        rag_engine = KairosContextEngine()
        rag_engine.reset_all()
        print("[Done] All RAG sessions wiped. Exiting.")
        sys.exit(0)

    def show_help():
        print("")
        print("  ┌─────────────────────────────────────────────────┐")
        print("  │  COMMANDS (type any of these at the prompt)     │")
        print("  ├─────────────────────────────────────────────────┤")
        print("  │  new       — Start a fresh session              │")
        print("  │  resume    — Continue a previous session        │")
        print("  │  sessions  — List all past sessions             │")
        print("  │  load      — Load an existing deliverable       │")
        print("  │  reset     — Clear all RAG memory               │")
        print("  │  help      — Show this menu                     │")
        print("  │  exit      — Quit Kairos                        │")
        print("  └─────────────────────────────────────────────────┘")
        print("")
        print("  Or just type your objective directly to start building!")
        print("")

    show_help()

    # ── Session Setup ──
    rag_engine = KairosContextEngine()
    session_id = ""
    deliverables_context = ""

    # Check if there are existing sessions to offer resume
    existing_sessions = rag_engine.list_all_sessions()
    if existing_sessions:
        print(f"  📂 You have {len(existing_sessions)} existing session(s).")
        print(f"     Type 'resume' to continue one, or press Enter for a new session.\n")

    # ── Main Command Loop ──
    active = True
    while active:
        try:
            user_cmd = input("kairos> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Kairos] Goodbye!")
            sys.exit(0)

        if not user_cmd:
            continue

        cmd_lower = user_cmd.lower()

        # ── Command: help ──
        if cmd_lower == "help":
            show_help()
            continue

        # ── Command: exit ──
        if cmd_lower in ("exit", "quit", "q"):
            print("[Kairos] Goodbye!")
            sys.exit(0)

        # ── Command: sessions ──
        if cmd_lower == "sessions":
            sessions = rag_engine.list_all_sessions()
            if not sessions:
                print("  No sessions found.\n")
            else:
                print(f"\n  {'ID':<45} {'Cmds':<6} {'First Objective'}")
                print(f"  {'─'*45} {'─'*6} {'─'*40}")
                for s in sessions:
                    obj_preview = s['first_objective'][:40]
                    print(f"  {s['id']:<45} {s['command_count']:<6} {obj_preview}")
                print("")
            continue

        # ── Command: reset ──
        if cmd_lower == "reset":
            confirm = input("  ⚠️  This will delete ALL session memory. Type 'yes' to confirm: ").strip().lower()
            if confirm == "yes":
                rag_engine.reset_all()
            else:
                print("  Reset cancelled.")
            continue

        # ── Command: resume ──
        if cmd_lower == "resume":
            sessions = rag_engine.list_all_sessions()
            if not sessions:
                print("  No sessions to resume. Starting new session instead.")
                session_id = rag_engine.start_new_session()
            else:
                print(f"\n  Available sessions:")
                for i, s in enumerate(sessions, 1):
                    obj_preview = s['first_objective'][:50]
                    print(f"  {i}. {s['id']} ({s['command_count']} cmds) — {obj_preview}")
                print("")
                choice = input("  Enter session number (or press Enter for most recent): ").strip()
                if not choice:
                    idx = len(sessions) - 1
                else:
                    try:
                        idx = int(choice) - 1
                    except ValueError:
                        print("  Invalid choice. Using most recent.")
                        idx = len(sessions) - 1

                if 0 <= idx < len(sessions):
                    session_id = sessions[idx]["id"]
                    rag_engine.resume_session(session_id)
                else:
                    print("  Invalid number. Using most recent.")
                    session_id = sessions[-1]["id"]
                    rag_engine.resume_session(session_id)
            continue

        # ── Command: new ──
        if cmd_lower == "new":
            session_id = rag_engine.start_new_session()
            print("  Ready for objectives. Type your goal below.\n")
            continue

        # ── Command: load ──
        if cmd_lower == "load":
            load_choice = input("  Enter deliverable folder name: ").strip()
            if load_choice:
                deliverable_path = os.path.join("deliverables", load_choice)
                if os.path.isdir(deliverable_path):
                    print(f"  [Loader] Reading files from {deliverable_path}...")
                    texts: list[str] = []
                    for root, _, files in os.walk(deliverable_path):
                        for file in files:
                            if file.endswith((".py", ".md", ".txt", ".json", ".js", ".html", ".css", ".env", ".example", ".toml")):
                                filepath = os.path.join(root, file)
                                relpath = os.path.relpath(filepath, deliverable_path)
                                try:
                                    with open(filepath, "r", encoding="utf-8") as f:
                                        content = f.read()
                                    texts.append(f"__FILE_START__::{str(relpath)}\n{content}\n__FILE_END__")  # type: ignore
                                except Exception:
                                    pass
                    deliverables_context = "\n\n".join(texts)
                    print(f"  [Loader] ✅ Loaded {len(texts)} source files as context.\n")
                else:
                    print(f"  [Loader] ⚠️ Folder '{load_choice}' not found in deliverables/.\n")
            continue

        # ── Anything else = Objective (start building!) ──
        # If no session is active, auto-start a new one
        if not session_id:
            session_id = rag_engine.start_new_session()

        # Support multi-line objectives: keep reading until empty line
        objective_lines = [user_cmd]
        if not user_cmd.endswith(".spec"):
            print("  (Continue typing, or press Enter on empty line to submit)")
            while True:
                try:
                    line = input(".. ")
                except EOFError:
                    break
                if line.strip() == "":
                    break
                objective_lines.append(line)

        raw_input = "\n".join(objective_lines).strip()

        # Spec-file support
        if raw_input.endswith(".spec") and os.path.isfile(raw_input):
            with open(raw_input, "r", encoding="utf-8") as spec_file:
                objective = spec_file.read().strip()
            print(f"  [Spec Loader] Loaded objective from: {raw_input}")
            print(f"  [Spec Loader] Objective length: {len(objective)} characters")
        else:
            objective = raw_input

        if not objective:
            print("  [Error] No objective provided. Try again.\n")
            continue

        objective = str(objective)
        print(f"\n  [Objective] {objective[:120]}{'...' if len(objective) > 120 else ''}")  # type: ignore
        print(f"  [Objective] Length: {len(objective)} characters")

        # ── Execute the Pipeline ──
        from langchain_core.messages import HumanMessage  # type: ignore
        print("  [Boot] Loading engine...", end=" ", flush=True)
        app = build_factory_graph()
        print("Ready.")

        config = {"configurable": {"thread_id": session_id}}

        initial_state = {
             "messages": [HumanMessage(content=objective)],
             "user_objective": objective,
             "human_approved": False,
             "shared_memory_buffer": {},
             "deliverables_context": deliverables_context,
             "rag_session_id": session_id,
        }

        print("\n--- PHASE 0: RAG CONTEXT SCAN ---")
        for output in app.stream(initial_state, config):
            for key, value in output.items():
                pass

        # Check if halted at RAG negotiation
        state_snap = app.get_state(config)
        if state_snap.next == ('rag_negotiation',):
            rag_negotiation_node(state_snap.values)
            # Update state with user's criteria decision
            rag_criteria = state_snap.values.get("rag_criteria", [])
            app.update_state(config, {"rag_criteria": rag_criteria})
            print("\n--- PHASE 1: INITIATING THINK TANK ---")
            for output in app.stream(None, config):
                for key, value in output.items():
                    pass

        # Check if halted at "huddle"
        state_snap = app.get_state(config)
        if state_snap.next == ('huddle',):
            huddle_node(state_snap.values)

            proceed = input("\n  [Director Input] Type 'proceed' to authorize Swarm Huddle (or 'modify' to reject): ")

            if proceed.strip().lower() == "proceed":
                print("\n--- PHASE 3: PARALLEL SWARM DEPLOYMENT ---")
                app.update_state(config, {"human_approved": True})
                for output in app.stream(None, config):
                    pass
            else:
                print("\n  [Swarm Halted] Execution rejected by Director.")
                print("  Returning to command menu.\n")
                continue

        # Check if halted at the second gate: System Upgrade PR
        state_snap_pr = app.get_state(config)
        if state_snap_pr.next == ('github_pr',):
            github_pr_node(state_snap_pr.values)

            if state_snap_pr.values.get("generated_tools"):
                approve_pr = input("\n  [Director Input] Type 'merge' to authorize Autonomous Github Commit: ")
                if approve_pr.strip().lower() == "merge":
                    print("\n--- PHASE 5: AUTONOMOUS METAPROGRAMMING DEPLOYMENT ---")
                    app.update_state(config, {"pr_approved": True})
                    for output in app.stream(None, config):
                        pass
                else:
                    print("\n  [Swarm Halted] Autonomous Code Commit rejected by Director.")
            else:
                app.update_state(config, {"pr_approved": True})
                for output in app.stream(None, config):
                    pass

        print("\n  ✅ Project Delivery Complete.")
        print("  Type another objective, or 'exit' to quit.\n")


if __name__ == "__main__":
    main()
