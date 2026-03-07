# Root launcher for evaluation pipeline (Execute -> Evaluate -> DFC).
# Usage: python run_evaluation.py

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from evaluation.run_pipeline import main

if __name__ == "__main__":
    main()
