# Root launcher for the Dial NL-to-SQL pipeline.
# Runs the full pipeline (Generate NL-LQP -> Tag -> RAG -> Translation) from the Dial/ subfolder.
# Usage: python run_dial_pipeline.py [--steps 1,2,3,4] or --step1 --step2 --step3 --step4

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_DIAL_DIR = _ROOT / "Dial"
if not _DIAL_DIR.is_dir():
    raise RuntimeError(f"Dial subfolder not found: {_DIAL_DIR}")

sys.path.insert(0, str(_DIAL_DIR))
import os
os.chdir(_DIAL_DIR)

from run_dial_pipeline import main

if __name__ == "__main__":
    main()
