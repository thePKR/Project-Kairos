"""
Kairos Constraint Decoder — Criteria Extraction & Conflict Detection
=====================================================================
Original design by Prakhar Rai.

After each command completes, the decoder uses the existing LLM to
extract what technical decisions were made that future commands must
respect. Also detects when past criteria may conflict with a new objective.
"""


class KairosConstraintDecoder:
    """
    Decoder-transformer component for the Kairos RAG system.
    - Extracts criteria from completed command results
    - Detects potential conflicts between past criteria and new objectives
    """

    def __init__(self):
        # Lazy-loaded LLM — only imported when actually called
        self._llm = None

    def _get_llm(self):
        """Lazy-load the LLM to avoid importing heavy libs at import time."""
        if self._llm is None:
            from src.utils import get_llm  # type: ignore
            self._llm = get_llm(role="core_reasoner")
        return self._llm

    def extract_criteria(
        self,
        objective: str,
        tech_stack: str,
        dep_graph: dict,
        final_files: dict
    ) -> list:
        """
        After a command completes, extract the key decisions that were made
        which future commands must respect.

        Returns a list of criteria strings, e.g.:
        ["Must use Python/FastAPI", "Database is Neo4j Aura", "JWT-based auth"]
        """
        modules_desc = "\n".join(
            f"  - {k}: {v}" for k, v in dep_graph.items()
        ) if dep_graph else "N/A"

        files_list = ", ".join(final_files.keys()) if final_files else "N/A"

        prompt = (
            f"A software command just completed successfully.\n\n"
            f"Objective: {objective}\n"
            f"Tech Stack: {tech_stack}\n"
            f"Modules built:\n{modules_desc}\n"
            f"Files generated: {files_list}\n\n"
            f"Extract the KEY TECHNICAL DECISIONS that were made which any "
            f"future command MUST respect and NOT violate. Focus on:\n"
            f"- Programming language / framework choices\n"
            f"- Database / storage decisions\n"
            f"- API patterns or protocols chosen\n"
            f"- Architecture patterns (monolith, microservices, etc.)\n"
            f"- Authentication / security approaches\n\n"
            f"Output ONLY a pipe-separated list of short criteria phrases.\n"
            f"Example: Must use Python/FastAPI | Database is Neo4j Aura | REST API pattern\n"
            f"Do NOT wrap in markdown. Output ONLY the pipe-separated line."
        )

        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            content = str(response.content).strip()

            # Clean markdown artifacts if present
            content = content.replace("```", "").strip()

            # Parse the pipe-separated criteria
            criteria = [c.strip() for c in content.split("|") if c.strip()]

            # Sanity filter — remove anything that looks like an error or is too long
            criteria = [c for c in criteria if len(c) < 200 and not c.lower().startswith("error")]

            if criteria:
                print(f"[RAG Decoder] Extracted {len(criteria)} criteria from this command.")
            return criteria

        except Exception as e:
            print(f"[RAG Decoder] Warning: LLM criteria extraction failed: {e}")
            # Fallback: generate basic criteria from what we know
            fallback = []
            if tech_stack:
                fallback.append(f"Tech stack: {tech_stack}")
            return fallback

    def detect_relevant_criteria(
        self,
        current_objective: str,
        current_session_criteria: list,
        cross_session_data: dict
    ) -> dict:
        """
        Analyze which past criteria are relevant to the current objective.

        Returns:
        {
            "current_session": [relevant criteria from this session],
            "cross_session": {session_id: {"criteria": [...], "objective": "..."}},
            "has_relevant": True/False
        }
        """
        result = {
            "current_session": current_session_criteria,
            "cross_session": {},
            "has_relevant": False
        }

        # Current session criteria are always relevant
        if current_session_criteria:
            result["has_relevant"] = True

        # Cross-session criteria — already filtered by keyword matching in context_engine
        if cross_session_data:
            result["cross_session"] = cross_session_data
            result["has_relevant"] = True

        return result

    def format_criteria_for_prompt(self, criteria_list: list) -> str:
        """
        Format criteria into a string suitable for injection into LLM prompts.
        """
        if not criteria_list:
            return ""

        lines = "\n".join(f"  • {c}" for c in criteria_list)
        return (
            "\n\n=== CRITERIA THAT MUST NOT BE VIOLATED (FROM PRIOR COMMANDS) ===\n"
            f"{lines}\n"
            "=== END CRITERIA ===\n"
        )
