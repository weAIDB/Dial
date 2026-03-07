# evaluation/step3_dfc.py
# Step 3: Calculate DFC (Dialect Feature Coverage) per item.
# For score=2: DFC=100; score=0: DFC=0; score=1: regex-based coverage over dialect features.

import re
from collections import defaultdict

from rules import ALL_CLASSIFICATION_RULES


# -----------------------------------------------------------------------------
# Build feature regex dict (dialect -> list of compiled patterns)
# -----------------------------------------------------------------------------
def build_feature_dict():
    feature_dict = defaultdict(list)
    for rule in ALL_CLASSIFICATION_RULES:
        if not rule.get("negative"):
            continue
        pattern = rule["pattern"]
        for db in rule.get("positive", []):
            db_key = db.lower()
            try:
                compiled_re = re.compile(pattern, re.IGNORECASE)
                feature_dict[db_key].append(compiled_re)
            except re.error:
                continue
    return feature_dict


DIALECT_FEATURES_DICT = build_feature_dict()


# -----------------------------------------------------------------------------
# Extract dialect features from SQL via regex
# -----------------------------------------------------------------------------
def extract_features(sql: str, db_type: str) -> set:
    if not isinstance(sql, str) or not sql.strip():
        return set()
    found = set()
    patterns = DIALECT_FEATURES_DICT.get(db_type.lower(), [])
    for pat in patterns:
        if pat.search(sql):
            found.add(pat.pattern)
    return found


# -----------------------------------------------------------------------------
# Compute DFC for a single item
# -----------------------------------------------------------------------------
def calculate_dfc_entry(gold_sql: str, pred_sql: str, engine: str, eval_score: int):
    """
    eval_score: 0 = not executable, 1 = executable but wrong, 2 = correct.
    Returns: (dfc_value or None, details_dict)
    """
    if eval_score == 2:
        return 100.0, {"strategy": "correct_result", "reason": "Execution is correct (Score 2)"}
    if eval_score == 0:
        return 0.0, {"strategy": "execution_failed", "reason": "Execution failed (Score 0)"}

    gold_feats = extract_features(gold_sql, engine)
    if not gold_feats:
        return None, {"strategy": "skipped", "reason": "No dialect features in Gold SQL"}

    pred_feats = extract_features(pred_sql, engine)
    hits = gold_feats.intersection(pred_feats)
    score = (len(hits) / len(gold_feats)) * 100.0
    return score, {
        "strategy": "regex_match",
        "gold_features": list(gold_feats),
        "pred_features": list(pred_feats),
        "hits": list(hits),
    }
