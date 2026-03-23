import time
from typing import Dict, Any
from src.state import KairosState
from src.utils import get_llm

def scout_node(state: KairosState) -> Dict[str, Any]:
    """LangGraph Node for the Scout."""
    print("[Scout] Waking up. Polling web data...")
    llm = get_llm(role="ingestion_scout")
    
    # 1. Mocking the INGESTION of a real headline
    mock_headline = "Unexpected 14% drop in solar panel tariffs across Asian markets detected in live trading logs."
    print(f"[Scout] Ingested Data: '{mock_headline}'")
    
    # 2. Making the Brain THINK
    prompt = (
        f"You are the Scout Agent of Project Kairos. "
        f"Analyze this data snippet: '{mock_headline}'. "
        f"Is this economically significant enough to require heavy analysis by an Econometrician agent? "
        f"Respond ONLY with 'YES' or 'NO'."
    )
    
    try:
        print("[Scout] Sending data to NVIDIA NIM (Nemotron)...")
        response = llm.invoke(prompt)
        print(f"[Scout] AI Response Check: {response.content}")
        
        # Determine routing based on Nemotron's 1-word answer
        if "YES" in response.content.upper():
             print("[Scout] Anomaly confirmed. Passing to Econometrician.")
             anomalies = state.get("anomalies_detected", [])
             anomalies.append(mock_headline)
             return {"current_agent": "econometrician", "anomalies_detected": anomalies}
        else:
             print("[Scout] Normal conditions. No further action needed.")
             return {"current_agent": "end"}
             
    except Exception as e:
        print(f"\n[Scout] ERROR Hitting API: {str(e)}")
        print(">> Check if you generated an API key at build.nvidia.com and placed it in your .env file!")
        return {"current_agent": "end"}
