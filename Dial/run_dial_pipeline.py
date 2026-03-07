# run_dial_pipeline.py
# Master script: runs the full Dial pipeline in order (paper flow).
# 1. Generate NL-LQP from natural language and schema.
# 2. Tag dialect-aware LQP (cascaded operator labeling + functional category mapping).
# 3. RAG retrieval on tagged NL-LQP for dialect knowledge.
# 4. Translation and feedback iteration (rag2sql: NL+LQP+retrieval -> SQL, execution check, semantic verification).
# Run from the Dial project root. Configure paths and API in conf/settings.py or environment.

import sys
import os
import argparse
from pathlib import Path

# Ensure Dial root is on path
DIAL_ROOT = Path(__file__).resolve().parent
if str(DIAL_ROOT) not in sys.path:
    sys.path.insert(0, str(DIAL_ROOT))
os.chdir(DIAL_ROOT)


def run_step1_generate_nl_lqp():
    """Generate dialect-agnostic NL-LQP from input questions and schema."""
    from src.nl_lqp.generate_nl_lqp import main_async
    import asyncio
    print("\n=== Step 1: Generate NL-LQP ===\n")
    asyncio.run(main_async())


def run_step2_tag_dialect_aware_lqp():
    """Tag dialect-sensitive operators and map to functional categories."""
    from src.nl_lqp.tag_dialect_aware_lqp import main_async
    import asyncio
    print("\n=== Step 2: Tag dialect-aware LQP ===\n")
    asyncio.run(main_async())


def run_step3_rag_retrieval():
    """Run RAG retrieval on tagged NL-LQP; output per-dialect result files for translation."""
    from src.knowledge.runner import main
    print("\n=== Step 3: RAG retrieval (HINT-KB) ===\n")
    main()


def run_step4_translation():
    """Run translation + execution verification + semantic check."""
    from src.translation.main import main as translation_main
    print("\n=== Step 4: Translation and feedback iteration ===\n")
    translation_main()


def main():
    parser = argparse.ArgumentParser(description="Run Dial pipeline: NL-LQP -> Tag -> RAG -> Translation")
    parser.add_argument(
        "--steps",
        type=str,
        default="1,2,3,4",
        help="Comma-separated step numbers to run (e.g. 1,2,3,4 or 3,4)",
    )
    parser.add_argument(
        "--step1",
        action="store_true",
        help="Run only step 1 (Generate NL-LQP)",
    )
    parser.add_argument(
        "--step2",
        action="store_true",
        help="Run only step 2 (Tag dialect-aware LQP)",
    )
    parser.add_argument(
        "--step3",
        action="store_true",
        help="Run only step 3 (RAG retrieval)",
    )
    parser.add_argument(
        "--step4",
        action="store_true",
        help="Run only step 4 (Translation)",
    )
    args = parser.parse_args()

    steps_to_run = []
    if args.step1 or args.step2 or args.step3 or args.step4:
        if args.step1:
            steps_to_run.append(1)
        if args.step2:
            steps_to_run.append(2)
        if args.step3:
            steps_to_run.append(3)
        if args.step4:
            steps_to_run.append(4)
    else:
        steps_to_run = [int(s.strip()) for s in args.steps.split(",") if s.strip()]

    if not steps_to_run:
        print("No steps selected. Use --steps 1,2,3,4 or --step1 --step2 etc.")
        return

    if 1 in steps_to_run:
        run_step1_generate_nl_lqp()
    if 2 in steps_to_run:
        run_step2_tag_dialect_aware_lqp()
    if 3 in steps_to_run:
        run_step3_rag_retrieval()
    if 4 in steps_to_run:
        run_step4_translation()

    print("\nPipeline run completed.")


if __name__ == "__main__":
    main()
