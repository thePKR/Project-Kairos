BUILD AN INDUSTRY KNOWLEDGE GRAPH WEBSITE — FULL SPECIFICATION

=== CORE PRODUCT ===
Build a fully functional, single-command MVP web application using Python and Streamlit.
The user types any industry name (e.g., "Solar Energy", "Fintech", "Real Estate").
The system scrapes reliable web sources, extracts key processes, definitions, terms, and relationships using an LLM, and renders an interactive, streaming visual Knowledge Graph in the browser.

=== TECH STACK (ALL FREE) ===
- Frontend/UI: Streamlit with streamlit-agraph for interactive graph visualization
- Web Scraping: BeautifulSoup4 + requests (concurrent scraping with ThreadPoolExecutor)
- LLM Extraction: NVIDIA NIM via OpenAI-compatible API (use environment variable NVIDIA_API_KEY)
- Database: Neo4j Aura Free Tier (use environment variables NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
- If Neo4j is unavailable, fall back to in-memory Python dict storage

=== ARCHITECTURE ===
Generate the following file structure:

1. main.py — Streamlit entry point. Contains the text input, triggers the pipeline, renders the streaming graph.
2. scraper/web_scraper.py — Uses BeautifulSoup to scrape Wikipedia and other free sources. Uses ThreadPoolExecutor for concurrent scraping of 3-5 URLs. Returns raw text.
3. ai/extractor.py — Sends scraped text to NVIDIA NIM LLM. Extracts structured JSON with: key_processes (list), definitions (list of {term, definition}), relationships (list of {source, target, relationship_type}). Uses streaming/chunked responses to yield partial results.
4. graph/neo4j_manager.py — Manages Neo4j connection. Implements MERGE queries for nodes and relationships. Every node gets metadata: access_count (int, starts at 1), last_accessed (datetime). On retrieval, increments access_count. Includes cull_stale_nodes() to delete nodes not accessed in 14 days with access_count < 5.
5. ui/visualizer.py — Renders the knowledge graph using streamlit-agraph. Accepts streaming node/edge data and updates the graph incrementally.
6. requirements.txt — All pip dependencies.
7. README.md — Setup instructions, .env configuration, and usage guide.

=== CRITICAL UX REQUIREMENT: STREAMING GRAPH ===
DO NOT wait for the entire pipeline to finish before showing results.
Implement a streaming architecture:
- At Second 3: The central industry node appears on screen
- At Second 6: The first 5 core "Processes" branch out from the center
- At Second 10: Definitions and sub-terms pop into existence
Use Streamlit's st.empty() container pattern to progressively update the graph as the LLM yields results.

=== CACHE STRATEGY ===
Before scraping, check Neo4j for an existing graph for the requested industry.
- If found (Cache Hit): Load and display instantly (<0.5 seconds). Increment access_count.
- If not found (Cache Miss): Run the full scrape → extract → build pipeline.

=== LRU NODE CULLING ===
Include a function that can be called periodically to clean up stale nodes:
- Delete Objective subgraphs where last_accessed > 14 days ago AND access_count < 5
- This keeps the database under the 50,000 node free tier limit indefinitely.

=== ERROR HANDLING ===
- If scraping fails, show a user-friendly error in Streamlit
- If LLM fails, fall back to displaying raw scraped text
- If Neo4j is unreachable, continue with in-memory storage and warn the user
