import sys
import os

# Ensure src path is accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.graph_manager import KairosGraphManager

def run_janitor():
    print("===================================")
    print("🧹 Kairos Memory LRU Janitor")
    print("===================================")
    manager = KairosGraphManager()
    manager.cull_forgotten_memories()
    print("Cleanup cycle complete.")

if __name__ == "__main__":
    run_janitor()
