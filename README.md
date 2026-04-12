<p align="center">
  <h1 align="center">SKI – Project Kairos</h1>
  <p align="center">
    <strong>The Unstoppable Engine</strong> — A sovereign AI manufacturing system that autonomously builds, trains, and deploys private reasoning models at $0 CAPEX.
  </p>
  <p align="center">
    <a href="#-quickstart"><strong>Quickstart</strong></a> ·
    <a href="#-kairos-slm-v2"><strong>SLM v2</strong></a> ·
    <a href="#-architecture"><strong>Architecture</strong></a> ·
    <a href="#-rag-context-engine"><strong>RAG</strong></a> ·
    <a href="#-commands"><strong>Commands</strong></a> ·
    <a href="#-contributing"><strong>Contributing</strong></a>
  </p>
</p>

> ⚠️ **Status: Internal Refinement** — The Kairos SLM v2 reasoning engine has completed initial training and is undergoing alignment tuning and benchmark validation. The model weights and updated inference pipeline will be pushed to this repository once internal quality gates are passed. The factory engine (this repo) is fully operational.

---

## What is Kairos?

**Project Kairos** is the continuous R&D and manufacturing engine operating under the **SKI** parent company. It is a multi-agent autonomous software factory that takes plain English objectives and delivers production-ready codebases — and more critically, it is the system that builds, trains, and iterates on the **Kairos SLM** series: private, edge-deployable reasoning models that cost nothing to run.

### 🏰 The Efficiency Moat ("Unclaimable AI")

Kairos is designed to be a **Business with No One Able to Claim It.**

- **$0 CAPEX:** All training runs on free-tier cloud GPUs (Google Colab T4, Modal.com A100 credits). No proprietary compute infrastructure.
- **Edge-Native Inference:** Models are quantized to 4-bit and served via a Rust inference engine. The v2 reasoning model runs in **<1GB RAM** on commodity hardware — no GPU required at inference.
- **AGPL-3.0 Shield:** The core engine is open-source under the strongest copyleft license. Anyone who wraps this as a service must open-source their stack. The technology is a public common.
- **Continuous Iteration:** Kairos is a factory, not a product. v1 → v2 → v3. By the time someone reverse-engineers one version, the next is already in alignment.

---

## 🧠 Kairos SLM v2

The second-generation Kairos Small Language Model is a **reasoning-first foundation model** — not a general chatbot, but a thinking engine trained to decompose problems, reason step-by-step, and know when it doesn't know.

### Training Pipeline

The v2 model was trained using a four-stage pipeline designed to maximize reasoning capability within extreme compute constraints:

```
Stage 1: Supervised Fine-Tuning (SFT)
         ├─ 10K curated reasoning traces generated from a 7B teacher model
         ├─ Traces filtered for correctness via ground-truth validation
         └─ Model learns the FORMAT of structured reasoning (<think> traces)

Stage 2: Group Relative Policy Optimization (GRPO)
         ├─ Reinforcement learning with verifiable rewards
         ├─ 8 candidate chains generated per problem, scored by rule-based verifiers
         ├─ Curriculum schedule: arithmetic → logic → competition math
         └─ Model learns to REASON, not just imitate

Stage 3: Direct Preference Optimization (DPO)
         ├─ Preference pairs encoding epistemic honesty
         ├─ Model learns to say "I don't have enough information" over hallucination
         └─ Constraint adherence baked into alignment

Stage 4: Process Reward Model (PRM) Training
         ├─ Step-level verification model (separate LoRA head)
         ├─ Scores each reasoning step as correct/incorrect
         └─ Used at inference for Best-of-N chain selection
```

### Architecture

| Component | Specification |
|---|---|
| Base Model | Decoder-only Transformer (1.5B parameters) |
| Attention | Grouped Query Attention (GQA), 2 KV heads |
| FFN | SwiGLU activation |
| Positional Encoding | Rotary Position Embeddings (RoPE) |
| Normalization | RMSNorm (pre-norm) |
| Context Window | 32,768 tokens |
| Inference Quantization | 4-bit (GPTQ/AWQ mixed precision) |
| Inference RAM | **~600MB** model + ~150MB KV cache |
| Training Method | SFT → GRPO → DPO → PRM |
| Training Compute | ~20 GPU-hours (Colab T4 + Modal A100 free credits) |
| Training Cost | **$0** |

### Inference: Test-Time Compute Scaling

Raw single-shot accuracy from a 1.5B model is limited by parameter count. Kairos compensates with **test-time compute scaling** — spending more compute at inference to produce higher-quality answers:

```
Query arrives
    │
    ▼
Generate N candidate reasoning chains (N=8-16)
    │
    ▼
Score each chain step-by-step via Process Reward Model
    │
    ▼
Return highest-scoring chain
```

This allows the 1.5B model to achieve reasoning quality competitive with models 3-5× its size, at the cost of proportionally higher latency (~2-4s per response vs ~200ms single-shot).

### Benchmark Status

> **Note:** These are internal evaluation numbers on held-out test sets. Independent third-party evaluation will be conducted before public weight release.

| Benchmark | Kairos SLM v2 (Best-of-16 + PRM) | Category |
|---|---|---|
| GSM8K | Under validation | Grade-school math reasoning |
| MATH-500 | Under validation | Competition mathematics |
| ARC-Challenge | Under validation | Multi-step logical reasoning |
| GPQA | Under validation | Graduate-level science Q&A |

Results will be published in the model card on HuggingFace upon release.

### What the Model Is (and Isn't)

**The model IS:**
- A reasoning foundation that thinks before it answers (visible `<think>` traces)
- A base that anyone can customize via LoRA fine-tuning for their domain
- Fully offline — zero data leaves the device, ever
- $0 to run, forever

**The model is NOT:**
- A replacement for frontier models (GPT-4, Gemini, Claude) on general tasks
- Multimodal — text only, no vision or audio
- Designed for open-ended creative writing or casual conversation

### Domain Customization

The v2 model is architected as a **reasoning base + domain adapter** system:

```
Frozen reasoning base (1.5B, shared)
         │
    LoRA Adapters (~10MB each, swappable)
         ├── kairos-code     ← software engineering reasoning
         ├── kairos-legal    ← contract and regulatory analysis
         ├── kairos-medical  ← clinical decision support
         └── kairos-custom   ← your domain, your data, 30 min to train
```

A fine-tuning template is included in the repository. Anyone can train a domain-specific adapter on a free Colab T4 in under an hour.

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

The Kairos factory operates as a 14-phase autonomous pipeline with crash recovery, cost tracking, and four-layer context compression:

```
src/
├── main.py              # while(true) engine loop + interactive CLI
├── state.py             # KairosState schema (serializable for checkpoints)
├── utils.py             # Multi-model LLM router (NIM, DeepSeek, GPT-OSS, Kimi)
├── cost_tracker.py      # Real-time token expenditure monitoring
├── checkpoint.py        # WAL session persistence + crash recovery
├── memory_janitor.py    # Storage rotation (memory files, sessions, checkpoints)
├── agents/
│   ├── think_tank.py    # Reasoner → Decomposer → Assigner swarm
│   ├── coordinator.py   # Multi-agent orchestration (research → implement → verify)
│   ├── archivist.py     # Historical context retrieval
│   ├── scout.py         # Anomaly detection
│   └── tool_maker.py    # Self-upgrade: generates new tools
├── context/
│   └── compressor.py    # 4-layer context compression (Snip → Micro → Summary → Emergency)
├── memory/
│   ├── file_memory.py   # File-based persistent memory (~/.kairos/memory/)
│   └── graph_manager.py # Neo4j CRUD (optional, graceful fallback)
├── tools/
│   └── base.py          # Unified tool interface + permission-gated registry
├── permissions/
│   └── gate.py          # 5-mode security (Default, Plan, Auto, YOLO, Custom)
├── rag/
│   ├── context_engine.py
│   └── constraint_decoder.py
├── sandbox/
│   └── executor.py      # Isolated execution + iterative auto-patching
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

**Resilience features:**
- **WAL Checkpointing:** State serialized after every phase. `kairos> resume` recovers from any crash.
- **4-Layer Context Compression:** Prevents token overflow in long sessions. Handles 128K+ token conversations gracefully.
- **Anti-Stub Detection:** Regex scans generated code for placeholder `pass`/`TODO` statements and rewrites them with real implementations.
- **Cost Tracking:** Real-time visibility into API token expenditure across all models.

**Human-in-the-Loop checkpoints:**
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

| | Vector RAG (OpenAI/Pinecone) | Kairos RAG |
|---|---|---|
| Retrieval latency | ~200–500ms | **<1ms** |
| Cost per retrieval | Embedding API call ($) | Zero (local file I/O) |
| Infrastructure | Vector DB required | **None** — just `.txt` files |
| Scales to millions? | Yes | No — but doesn't need to |

---

## 📟 Commands

After launching with `moment`, you get an interactive prompt:

```
╔══════════════════════════════════════════════════════╗
║             SKI — PROJECT KAIROS                    ║
║       Autonomous AI Manufacturing Engine             ║
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
| `gc` | Run storage rotation (memory janitor) |
| `cost` | Display session token expenditure |
| `doctor` | Run environment diagnostics |
| `help` | Show available commands |
| `exit` | Quit Kairos |
| *(anything else)* | Treated as an objective — starts building |

You can also type a `.spec` file path to load long objectives from a file.

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
├── src/                    # Factory engine source
│   ├── main.py             # Core engine loop
│   ├── agents/             # Think-Tank + Coordinator swarm
│   ├── context/            # 4-layer compression pipeline
│   ├── memory/             # File-based + Neo4j memory
│   ├── tools/              # Tool interface + registry
│   ├── permissions/        # Permission gate system
│   ├── rag/                # Session-based context engine
│   ├── sandbox/            # Code execution sandbox
│   └── resources/          # Static data
├── slm/                    # SLM v2 training pipeline (coming soon)
│   ├── train_sft.py        # Stage 1: Supervised fine-tuning
│   ├── train_grpo.py       # Stage 2: GRPO reinforcement learning
│   ├── train_dpo.py        # Stage 3: DPO alignment
│   ├── train_prm.py        # Stage 4: Process reward model
│   └── finetune_domain.py  # Domain LoRA adapter template
├── deliverables/           # Generated project outputs
├── specs/                  # Objective spec files
├── BIZ_SPEC.md             # Business specification
├── GOVERNANCE.md           # SKI governance model
├── .env.example            # API key template
├── pyproject.toml          # Package config + `moment` entry point
├── requirements.txt        # Python dependencies
├── CONTRIBUTING.md         # Contribution guide
├── CODE_OF_CONDUCT.md      # Community standards
└── LICENSE                 # AGPL-3.0
```

---

## 🗺 Roadmap

- [x] Factory engine (14-phase autonomous pipeline)
- [x] Multi-model LLM routing (NIM, DeepSeek, GPT-OSS, Kimi)
- [x] Session-based RAG with cross-session constraint retrieval
- [x] WAL checkpointing + crash recovery
- [x] 4-layer context compression
- [x] File-based persistent memory system
- [x] Permission gate (5-mode security)
- [x] Cost tracking singleton
- [x] SLM v2 architecture design + training pipeline
- [x] SLM v2 SFT + GRPO training (initial pass)
- [ ] SLM v2 DPO alignment tuning (in progress)
- [ ] SLM v2 PRM training + Best-of-N inference (in progress)
- [ ] SLM v2 benchmark validation + model card
- [ ] SLM v2 public weight release on HuggingFace
- [ ] Domain LoRA adapter templates (code, legal, medical)
- [ ] Rust inference engine (Candle) with speculative decoding
- [ ] One-click installer for non-technical users

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and pull request guidelines.

---

## 📄 License

**Project Kairos** is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This ensures that the core manufacturing engine remains an open, unclaimable public common. Any commercial SaaS that attempts to wrap or host this network engine must release their modified source code back to the community.

See the `LICENSE` file for details, and read `GOVERNANCE.md` to understand the division between the open-source Kairos engine and the tailored enterprise deployments handled by SKI.
