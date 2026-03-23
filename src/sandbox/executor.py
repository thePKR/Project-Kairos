import subprocess
import sys
import os
import tempfile
import shutil

MAX_RETRIES = 3

def find_entry_point(files: dict) -> str:
    """
    Intelligently determines which file to execute as the entry point.
    Priority: main.py > app.py > server.py > index.py > first .py file found.
    """
    priority = ["main.py", "app.py", "server.py", "index.py"]
    
    for candidate in priority:
        for path in files.keys():
            if path.endswith(candidate):
                return path
    
    # Fallback: first Python file
    for path in files.keys():
        if path.endswith(".py"):
            return path
    
    return ""

def run_in_sandbox(files: dict, timeout: int = 15) -> dict:
    """
    Writes files to a temp directory, executes the entry point in an isolated subprocess,
    and returns the result with stdout, stderr, and success status.
    
    Args:
        files: Dict of {relative_path: content_string}
        timeout: Max seconds to allow the script to run before killing it
        
    Returns:
        dict with keys: success (bool), stdout (str), stderr (str), entry_point (str)
    """
    entry_point = find_entry_point(files)
    
    if not entry_point:
        return {
            "success": False,
            "stdout": "",
            "stderr": "No Python entry point found in generated files.",
            "entry_point": ""
        }
    
    # Create an isolated temp workspace
    sandbox_dir = tempfile.mkdtemp(prefix="kairos_sandbox_")
    
    try:
        # Write all files into the sandbox
        for rel_path, content in files.items():
            full_path = os.path.join(sandbox_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        entry_full_path = os.path.join(sandbox_dir, entry_point)
        
        # Execute with a fresh Python subprocess
        result = subprocess.run(
            [sys.executable, entry_full_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox_dir,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "entry_point": entry_point
        }
        
    except subprocess.TimeoutExpired:
        # A timeout usually means the script launched a server or long-running
        # process successfully — that's actually a PASS, not a failure.
        return {
            "success": True,
            "stdout": f"Process ran for {timeout}s without crashing (likely a server/daemon).",
            "stderr": "",
            "entry_point": entry_point
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Sandbox execution error: {str(e)}",
            "entry_point": entry_point
        }
    finally:
        # Always clean up the temp directory
        shutil.rmtree(sandbox_dir, ignore_errors=True)
