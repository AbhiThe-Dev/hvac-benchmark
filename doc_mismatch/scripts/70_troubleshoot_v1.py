"""Technician-guided troubleshooting, working model v1 (see TROUBLESHOOT_V1.md). Uses no trend data; every unmarked number is a placeholder.
  .venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py                                  # interactive, on the made-up example building (richest tier its file supports)
  .venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py --demo --tier T3 --truth low_static   # a simulated technician answers (illustration only, not a result)
  .venv/bin/python doc_mismatch/scripts/70_troubleshoot_v1.py --tier T0 --member Room-204 --room-name "Room 204"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch.troubleshoot.v1.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
