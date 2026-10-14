"""Technician-guided troubleshooting, working model v0 (see TROUBLESHOOT.md). Uses no trend data.
  .venv/bin/python doc_mismatch/scripts/61_troubleshoot.py                # interactive, on the made-up example building
  .venv/bin/python doc_mismatch/scripts/61_troubleshoot.py --demo         # a simulated technician answers (illustration only, not a result)
  .venv/bin/python doc_mismatch/scripts/61_troubleshoot.py --building my.json --member Room-204 --airflow no
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docmismatch.troubleshoot.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
