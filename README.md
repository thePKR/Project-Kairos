# Project Kairos: Autonomous Software Factory 🏭🧠

Project Kairos is an advanced, multi-agent orchestration framework utilizing **LangGraph**, **NVIDIA NIM**, **DeepSeek**, and **Neo4j**. It is designed as an Objective-Driven Software Factory capable of generating extremely dense AI analysis, dynamically analyzing internal capability gaps, writing its own Python tools, and pushing them autonomously to its own Git repository.

## ⚡ Zero-Config Quick Start
Deploy the autonomous swarm on your local machine in under 60 seconds.

```bash
git clone https://github.com/thePKR/Project-Kairos.git
cd Project-Kairos
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
1. Copy `.env.example` to `.env` and insert your free NVIDIA NIM API key.
2. Wake up the Factory:
```bash
python src/main.py
```
> **Hello World Objective:** `"Analyze optimal capital allocation strategies for commercial banks under strict ESG constraints."`

---

## 🏗 The Architecture
The Swarm is completely decoupled from heavy VRAM hardware constraints by splitting the cognitive architecture into Cloud/Local layers:
- **The Engine (Local Chaos):** A lightweight Python/LangGraph control loop managing state buffers with zero local VRAM overhead.
- **The Brain (Cloud APIs):** Intelligent LLM routing connects specific tasks to their optimal architectures (DeepSeek for persistent coding, GPT-OSS for private reasoning, NVIDIA Nemotron for massive 1M context ingestion).
- **The Memory (Neo4j Aura):** Contextual relations are offloaded to a free-tier Cloud Graph database.

## System Workflow
1. **The Think-Tank Phase (Phase 1):** The `Reasoner` and `Decomposer` interact to dynamically map an Objective into a JSON dependency graph of constraints and execution modules.
2. **The Huddle (Phase 2):** Utilizing LangGraph `MemorySaver` checkpointers, the system halts execution mid-air, presenting the Director with a generated Gantt-style roadmap and Risk Summary. Awaits CLI `Proceed` authorization.
3. **Parallel Swarm Deployment (Phase 3):** Virtual LLM workers parse the JSON state, synthesize the markdown or code, and populate the `shared_memory_buffer` managed by the Librarian node.
4. **Validation Gate (Phase 4):** Cross-peer AST review of generated python objects against the initial constraints. 
5. **Autonomous Meta-Programming CI/CD (Phase 5):** If the Swarm wrote new python tools (`.py`), the system triggers a second interrupt gate (The PR Review). Once approved, the Delivery Node writes the scripts to disk and automatically triggers `git add`, `git commit`, and `git push` to upgrade its own repository without human coding interaction.

## Getting Started
Ensure you have created your `.env` file correctly, then deploy the swarm:
```powershell
python src/main.py
```
Awaiting your objective...
