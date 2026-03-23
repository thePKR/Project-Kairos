import os
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

def get_llm(role: str = "general"):
    """
    Dynamically switches models and providers based on the agent's needs.
    Safely routes to NVIDIA NIM via the generic OpenAI integration pattern.
    """
    nv_key = os.getenv("NVIDIA_API_KEY", "")
    
    # Using LangChain's generic OpenAI wrapper pointed at NVIDIA's servers (highly reliable)
    nvidia_fallback = ChatOpenAI(
        model="meta/llama-3.3-70b-instruct",
        api_key=nv_key,
        base_url="https://integrate.api.nvidia.com/v1"
    )

    if role == "ingestion_scout":
        return nvidia_fallback
        
    elif role == "systems_engineer":
        ds_key = os.getenv("DEEPSEEK_API_KEY", "")
        if ds_key and "your_deepseek" not in ds_key:
            return ChatOpenAI(
                model="deepseek-v3.2", 
                api_key=ds_key,
                base_url="https://api.deepseek.com/v1"
            )
        return nvidia_fallback
        
    elif role == "core_reasoner":
        oss_key = os.getenv("GPT_OSS_API_KEY", "")
        if oss_key and "your_gpt_oss" not in oss_key:
            return ChatOpenAI(
                model="gpt-oss-120b",
                api_key=oss_key,
                base_url=os.getenv("GPT_OSS_BASE_URL", "http://localhost:8000/v1")
            )
        return nvidia_fallback
        
    elif role == "swarm_visualizer":
        kimi_key = os.getenv("KIMI_API_KEY", "")
        if kimi_key and "your_kimi" not in kimi_key:
            return ChatOpenAI(
                model="kimi-k2.5",
                api_key=kimi_key,
                base_url="https://api.moonshot.cn/v1" 
            )
        return nvidia_fallback
        
    else:
        return nvidia_fallback

def get_neo4j_driver():
    """Fetch the Neo4j AuraDB driver."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(username, password))
