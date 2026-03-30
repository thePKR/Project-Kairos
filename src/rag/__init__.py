"""
Kairos RAG — Session-Based Context Engine
==========================================
Original design by Prakhar Rai.

A file-based retrieval system where each session stores all commands
in a single log file. Prior commands become criteria that must not
be violated. Sessions can be cross-read for relevant context.
"""

from src.rag.context_engine import KairosContextEngine  # type: ignore
from src.rag.constraint_decoder import KairosConstraintDecoder  # type: ignore

__all__ = ["KairosContextEngine", "KairosConstraintDecoder"]
