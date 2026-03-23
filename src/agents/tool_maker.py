import os
from typing import Dict, Any
import docker
from docker.errors import DockerException

class DockerSandbox:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException:
            print("[Warning] Docker daemon not running or inaccessible.")
            self.client = None

    def execute_script(self, script_content: str) -> tuple[int, str]:
        """Runs synthesized python code safely in an isolated offline container."""
        if not self.client:
            return 1, "Docker client unavailable"
            
        print("[Sandbox] Provisioning python:3.11-slim container...")
        try:
            container = self.client.containers.run(
                "python:3.11-slim",
                command=["python", "-c", script_content],
                mem_limit="512m",
                network_disabled=True, 
                detach=True
            )
            
            # Wait with a 10 second timeout against infinite loops
            result = container.wait(timeout=10)
            logs = container.logs().decode("utf-8")
            
            # Cleanup
            container.remove()
            
            return result.get('StatusCode', 1), logs
            
        except Exception as e:
            return 1, f"Sandbox Error: {str(e)}"

def tool_maker_node(state: dict) -> Dict[str, Any]:
    """LangGraph Node for the Tool-Maker."""
    requests = state.get("tool_requests", [])
    if not requests:
        return {"current_agent": "econometrician"}
        
    latest_request = requests[-1]
    print(f"[Tool-Maker] Synthesizing code for request: {latest_request.get('purpose')}")
    
    # Placeholder: The NIM LLM would generate this code dynamically
    mock_script = "print('Custom GARCH volatility matrix initialized successfully.')"
    
    sandbox = DockerSandbox()
    status_code, logs = sandbox.execute_script(mock_script)
    
    if status_code == 0:
        print(f"[Tool-Maker] Script Execution Success:\n{logs}")
        # Here we would persist it to the SQLite Tool Library DB
    else:
        print(f"[Tool-Maker] Script Failed. Traceback:\n{logs}")
    
    return {"current_agent": "econometrician"}
