"""Absolute path resolution for project data and indexes.

Centralizes filesystem layout so that scripts and library code agree on where
raw documents, processed chunks, and the vector index live. Paths are computed
relative to the repository root (parent of the ``src/`` directory) regardless
of the caller's current working directory.
"""

from __future__ import annotations

from pathlib import Path

# __file__ = .../src/vietnam_legal_rag/paths.py
# parents[0] = .../src/vietnam_legal_rag/
# parents[1] = .../src/
# parents[2] = .../  (repo root)
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
EVAL_DIR: Path = DATA_DIR / "eval"
INDEX_DIR: Path = DATA_DIR / "index"

# Ensure the persistent data directories exist for first-time use.
for _p in (RAW_DIR, PROCESSED_DIR, EVAL_DIR):
    _p.mkdir(parents=True, exist_ok=True)
    # Touch the .gitkeep if absent so the directory survives a fresh clone.
    if not any(_p.iterdir()):
        (_p / ".gitkeep").touch(exist_ok=True)


def relative_to_repo(path: Path) -> Path:
    """Return ``path`` made relative to the repo root if it is underneath it."""
    try:
        return path.relative_to(PROJECT_ROOT)
    except ValueError:
        return path


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DIR",
    "PROCESSED_DIR",
    "EVAL_DIR",
    "INDEX_DIR",
    "relative_to_repo",
]
