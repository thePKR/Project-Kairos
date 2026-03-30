<p align="center">
  <h1 align="center">Project Kairos</h1>
  <p align="center">
    <strong>Autonomous Software Factory</strong> — An objective-driven AI swarm that reasons, plans, builds, validates, and self-upgrades.
  </p>
  <p align="center">
    <a href="#-quickstart"><strong>Quickstart</strong></a> ·
    <a href="#-architecture"><strong>Architecture</strong></a> ·
    <a href="#-rag-context-engine"><strong>RAG</strong></a> ·
    <a href="#-commands"><strong>Commands</strong></a> ·
    <a href="#-contributing"><strong>Contributing</strong></a>
  </p>
</p>

---

## What is Kairos?

Kairos is a multi-agent orchestration framework built on **LangGraph**. Give it an objective in plain English — it reasons through constraints, decomposes the work into modules, synthesizes code in parallel, validates it in a sandbox, and delivers a working file tree. If it writes new Python tools for itself, it can autonomously commit them to its own repository.

The system is fully decoupled from local GPU hardware:

| Layer | Where | What |
|-------|-------|------|
| **Engine** | Local | Lightweight Python/LangGraph control loop, zero VRAM |
| **Brain** | Cloud APIs | NVIDIA NIM · DeepSeek · GPT-OSS · Kimi — routed per task |
| **Memory** | Neo4j Aura | Free-tier graph DB for long-term objective archival |
| **RAG** | Local Files | Session-based context engine with cross-session retrieval |

---

## ⚡ Quickstart

### Prerequisites
- Python ≥ 3.10
- A free [NVIDIA NIM](https://build.nvidia.com) API key

### Install

```bash
git clone https://github.com/thePKR/Project-Kairos.git
cd Project-Kairos
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -e .
```

### Configure

```bash
cp .env.example .env
# Edit .env and insert your API keys
```

### Run

```bash
moment
```

That's it. The `moment` command is registered globally when you `pip install -e .` — works from any directory.

> **First objective to try:**  
> `"Create a FastAPI server that exposes a knowledge graph of the renewable energy industry using Neo4j."`

---

## 🏗 Architecture

```
src/
├── main.py              # LangGraph state machine + interactive CLI
├── state.py             # KairosState TypedDict (shared state schema)
├── utils.py             # LLM router (NVIDIA NIM, DeepSeek, GPT-OSS, Kimi)
├── memory_janitor.py    # LRU cleanup for Neo4j graph memory
├── agents/
│   ├── think_tank.py    # Reasoner → Decomposer → Assigner pipeline
│   ├── archivist.py     # Historical context retrieval
│   ├── scout.py         # Anomaly detection agent
│   └── tool_maker.py    # Self-upgrade: generates new Python tools
├── memory/
│   └── graph_manager.py # Neo4j CRUD for objective/task/file graphs
├── rag/                 # ← NEW: Session-based context engine
│   ├── context_engine.py
│   └── constraint_decoder.py
├── sandbox/
│   └── executor.py      # Isolated subprocess execution + error capture
└── resources/
    └── known_packages.json
```

### Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ RAG Context │───→│   Memory     │───→│   Think-Tank     │───→│   Huddle    │
│   Scan      │    │  Retrieval   │    │ Reason→Decompose │    │  (Approve?) │
└─────────────┘    └──────────────┘    │  →Assign         │    └──────┬──────┘
                                       └──────────────────┘           │
                                                                      ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│  Delivery   │◄───│  Validation  │◄───│    Sandbox       │◄───│  Parallel   │
│  + RAG Log  │    │  Gate (AST)  │    │  (Self-Correct)  │    │  Execution  │
└─────────────┘    └──────────────┘    └──────────────────┘    └─────────────┘
```

**Human-in-the-Loop checkpoints:** The pipeline pauses at three gates for your approval:
1. **RAG Negotiation** — Review prior criteria before the Think-Tank runs
2. **The Huddle** — Approve the proposed work plan
3. **PR Review** — Authorize system self-upgrades before git commit

---

## 🧠 RAG Context Engine

> *Original design by Prakhar Rai*

Kairos has its own file-based Retrieval-Augmented Generation system. It's not a vector database — it's faster.

### How it works

- **One session = one log file.** All commands within a session are appended to a single `.txt` file in `src/rag/sessions/`.
- **Criteria accumulate.** After each command completes, Kairos extracts the key technical decisions (e.g., "Must use FastAPI", "Database is Neo4j") and logs them.
- **Prior criteria = rules that must not be violated.** On every new command, Kairos reads the log, presents prior criteria, and asks you: *proceed, modify, or ignore?*
- **Cross-session reading.** When starting a new objective, Kairos scans ALL past session logs for relevant criteria via keyword matching — no embeddings, no API calls, just fast regex.

### Why not vector-based RAG?

| | Vector RAG (OpenAI/Pinecone) | Kairos RAG |
|---|---|---|
| Retrieval latency | ~200–500ms | **<1ms** |
| Cost per retrieval | Embedding API call ($) | Zero (local file I/O) |
| Infrastructure | Vector DB required | **None** — just `.txt` files |
| Scales to millions? | Yes | No — but doesn't need to |

Kairos isn't searching Wikipedia. It's reading its own command history — regex on a few KB of text will always be faster than a network roundtrip to a vector database.

---

## 📟 Commands

After launching with `moment`, you get an interactive prompt:

```
╔══════════════════════════════════════════════════════╗
║         PROJECT KAIROS — Software Factory           ║
║           Autonomous AI Build System                 ║
╚══════════════════════════════════════════════════════╝

kairos>
```

| Command | Action |
|---------|--------|
| `new` | Start a fresh session |
| `resume` | Continue a previous session |
| `sessions` | List all past sessions |
| `load` | Load an existing deliverable folder as context |
| `reset` | Clear all RAG session memory |
| `help` | Show available commands |
| `exit` | Quit Kairos |
| *(anything else)* | Treated as an objective — starts building |

You can also type a `.spec` file path to load long objectives from a file.

### CLI Flags

```bash
moment --reset-rag    # Wipe all session memory and exit
```

---

## 🔧 Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```env
# Required — get a free key at build.nvidia.com
NVIDIA_API_KEY=nvapi-xxxxx

# Optional — enables DeepSeek for systems engineering tasks
DEEPSEEK_API_KEY=your_key_here

# Optional — Neo4j Aura for long-term graph memory
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

Only `NVIDIA_API_KEY` is required. Everything else gracefully falls back.

---

## 📂 Project Structure

```
Project-Kairos/
├── src/                    # Core source code
│   ├── main.py             # Entry point + state machine
│   ├── agents/             # Think-Tank agents
│   ├── memory/             # Neo4j graph manager
│   ├── rag/                # Session-based context engine
│   ├── sandbox/            # Code execution sandbox
│   └── resources/          # Static data (known packages)
├── deliverables/           # Generated project outputs (gitignored)
├── specs/                  # Objective spec files
├── .env.example            # API key template
├── pyproject.toml          # Package config + `moment` entry point
├── requirements.txt        # Python dependencies
├── CONTRIBUTING.md         # Contribution guide
└── CODE_OF_CONDUCT.md      # Community standards
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and pull request guidelines.

---

## 📄 License

This project is open source. See the repository for license details.
