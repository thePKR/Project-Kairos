"""
Kairos Context Engine — Session-Based File RAG
================================================
Original design by Prakhar Rai.

Manages session log files: one .txt file per session, all commands
appended within. Supports cross-session reading and criteria extraction
via fast regex scanning.
"""

import os
import re
import datetime
import glob

# The sessions directory lives alongside this file
_RAG_DIR = os.path.dirname(os.path.abspath(__file__))
_SESSIONS_DIR = os.path.join(_RAG_DIR, "sessions")


class KairosContextEngine:
    """
    Core engine for Kairos RAG.
    - Each session = one .txt log file
    - All commands within a session are appended to that file
    - Cross-reads all sessions to find relevant criteria
    """

    def __init__(self, session_id: str = ""):
        os.makedirs(_SESSIONS_DIR, exist_ok=True)
        self._session_id = session_id
        self._session_path = ""
        self._command_count = 0

    # ──────────────────────────────────────────
    # Session Management
    # ──────────────────────────────────────────

    def start_new_session(self) -> str:
        """Create a new session file with a header. Returns session ID."""
        existing = self.list_all_sessions()
        next_num = len(existing) + 1
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._session_id = f"session_{next_num:03d}_{now}"
        self._session_path = os.path.join(_SESSIONS_DIR, f"{self._session_id}.txt")
        self._command_count = 0

        header = (
            f"╔══════════════════════════════════════════════════════════════╗\n"
            f"║  KAIROS SESSION #{next_num:03d} — Started {now}       ║\n"
            f"╚══════════════════════════════════════════════════════════════╝\n\n"
        )
        with open(self._session_path, "w", encoding="utf-8") as f:
            f.write(header)

        print(f"[RAG] New session started: {self._session_id}")
        return self._session_id

    def resume_session(self, session_id: str) -> bool:
        """Resume an existing session. Returns True if successful."""
        path = os.path.join(_SESSIONS_DIR, f"{session_id}.txt")
        if not os.path.exists(path):
            print(f"[RAG] Session '{session_id}' not found.")
            return False

        self._session_id = session_id
        self._session_path = path

        # Count existing commands in the session
        content = self._read_file(path)
        self._command_count = len(re.findall(r"\[CMD #(\d+)\]", content))

        print(f"[RAG] Resumed session: {session_id} ({self._command_count} commands)")
        return True

    def list_all_sessions(self) -> list:
        """List all session files, sorted by name (chronological)."""
        pattern = os.path.join(_SESSIONS_DIR, "session_*.txt")
        files = sorted(glob.glob(pattern))
        sessions = []
        for f in files:
            basename = os.path.splitext(os.path.basename(f))[0]
            # Extract first objective from the session for display
            content = self._read_file(f)
            first_obj_match = re.search(r"OBJECTIVE:\s*(.+)", content)
            first_obj = first_obj_match.group(1).strip() if first_obj_match else "(empty session)"
            cmd_count = len(re.findall(r"\[CMD #(\d+)\]", content))
            sessions.append({
                "id": basename,
                "path": f,
                "first_objective": first_obj,
                "command_count": cmd_count
            })
        return sessions

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def command_count(self) -> int:
        return self._command_count

    # ──────────────────────────────────────────
    # Log I/O
    # ──────────────────────────────────────────

    def commit_command(
        self,
        objective: str,
        tech_stack: str,
        modules: list,
        outcome: str,
        criteria: list,
        user_override: str = "None"
    ):
        """Append a command block to the current session file."""
        if not self._session_path:
            print("[RAG] Warning: No active session. Cannot commit.")
            return

        self._command_count += 1
        now = datetime.datetime.now().isoformat()
        modules_str = " | ".join(modules) if modules else "N/A"
        criteria_str = " | ".join(criteria) if criteria else "None"

        block = (
            f"\n══════════════════════════════════════════\n"
            f"[CMD #{self._command_count:03d}] {now}\n"
            f"══════════════════════════════════════════\n"
            f"OBJECTIVE: {objective}\n"
            f"TECH_STACK: {tech_stack}\n"
            f"MODULES: {modules_str}\n"
            f"OUTCOME: {outcome}\n"
            f"CRITERIA: {criteria_str}\n"
            f"USER_OVERRIDE: {user_override}\n"
            f"──────────────────────────────────────────\n"
        )

        with open(self._session_path, "a", encoding="utf-8") as f:
            f.write(block)

        print(f"[RAG] Command #{self._command_count} logged to session.")

    # ──────────────────────────────────────────
    # Criteria Scanning (Fast Regex)
    # ──────────────────────────────────────────

    def load_current_session_criteria(self) -> list:
        """Read the current session file and extract all unique criteria."""
        if not self._session_path or not os.path.exists(self._session_path):
            return []
        content = self._read_file(self._session_path)
        return self._extract_criteria(content)

    def load_all_criteria(self) -> dict:
        """
        Scan every session file. Returns {session_id: [criteria_list]}.
        This is the cross-read capability.
        """
        result = {}
        for session in self.list_all_sessions():
            content = self._read_file(session["path"])
            criteria = self._extract_criteria(content)
            if criteria:
                result[session["id"]] = {
                    "criteria": criteria,
                    "first_objective": session["first_objective"],
                    "command_count": session["command_count"]
                }
        return result

    def cross_read(self, current_objective: str) -> dict:
        """
        Scan all OTHER sessions for criteria relevant to the current objective.
        Uses keyword matching on objectives.
        Returns {session_id: {criteria: [...], objective: "..."}} for relevant sessions.
        """
        if not current_objective:
            return {}

        # Extract meaningful keywords from the current objective (3+ chars, skip stopwords)
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "use", "used",
            "make", "made", "create", "build", "for", "with", "from", "into",
            "that", "this", "these", "those", "and", "but", "not", "also", "too",
            "very", "just", "about", "above", "below", "to", "of", "in", "on",
            "at", "by", "up", "out", "off", "over", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why", "how", "all",
            "each", "every", "both", "few", "more", "most", "other", "some", "such",
            "only", "own", "same", "so", "than", "it", "its", "get", "add", "code",
        }
        keywords = [
            w.lower() for w in re.findall(r'\w+', current_objective)
            if len(w) >= 3 and w.lower() not in stopwords
        ]

        if not keywords:
            return {}

        relevant = {}
        for session in self.list_all_sessions():
            # Skip the current active session
            if session["id"] == self._session_id:
                continue

            content = self._read_file(session["path"])
            content_lower = content.lower()

            # Check if any keyword appears in the session content
            matches = sum(1 for kw in keywords if kw in content_lower)
            if matches >= 1:  # At least 1 keyword match
                criteria = self._extract_criteria(content)
                if criteria:
                    relevant[session["id"]] = {
                        "criteria": criteria,
                        "first_objective": session["first_objective"],
                        "match_score": matches
                    }

        return relevant

    # ──────────────────────────────────────────
    # Housekeeping
    # ──────────────────────────────────────────

    def reset_all(self):
        """Delete all session files. Only call on explicit user request."""
        sessions = self.list_all_sessions()
        for s in sessions:
            try:
                os.remove(s["path"])
            except OSError:
                pass
        self._session_id = ""
        self._session_path = ""
        self._command_count = 0
        print(f"[RAG] All {len(sessions)} session(s) cleared.")

    def reset_session(self, session_id: str):
        """Delete a specific session file."""
        path = os.path.join(_SESSIONS_DIR, f"{session_id}.txt")
        if os.path.exists(path):
            os.remove(path)
            print(f"[RAG] Session '{session_id}' deleted.")
        else:
            print(f"[RAG] Session '{session_id}' not found.")

    # ──────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────

    def _read_file(self, path: str) -> str:
        """Read a file safely, return empty string on failure."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _extract_criteria(self, content: str) -> list:
        """
        Regex-extract all CRITERIA lines from session content.
        Returns deduplicated list in order of appearance.
        """
        matches = re.findall(r"CRITERIA:\s*(.+)", content)
        seen = set()
        criteria = []
        for match in matches:
            items = [item.strip() for item in match.split("|")]
            for item in items:
                item_lower = item.lower()
                if item_lower and item_lower != "none" and item_lower not in seen:
                    seen.add(item_lower)
                    criteria.append(item)
        return criteria
