# knowledge_process/knowledge_create.py
# Extracts official documentation from any dialect/source into the dialect knowledge format.
# Supports: Git repos (e.g. DuckDB, PostgreSQL docs), or local doc directories.
# Output: @dialect2sql@-delimited blocks for use by tide_rule / tide_functional_knowledge.
# Configure TARGET_DIALECT, source path, and output path in CONFIG.

import os
import re
import subprocess
import sys
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================
# Target dialect name (used in output labels, e.g. "DuckDB", "PostgreSQL", "Oracle").
TARGET_DIALECT = os.environ.get("KNOWLEDGE_TARGET_DIALECT", "DuckDB")

# Source: "git" = clone from GIT_REPO_URL; "local" = use LOCAL_DOCS_PATH directly.
SOURCE_TYPE = os.environ.get("KNOWLEDGE_SOURCE_TYPE", "git")

# For SOURCE_TYPE="git":
WORK_DIR = os.environ.get("KNOWLEDGE_WORK_DIR", "")
GIT_REPO_URL = os.environ.get("KNOWLEDGE_GIT_REPO_URL", "")
LOCAL_REPO_NAME = os.environ.get("KNOWLEDGE_LOCAL_REPO_NAME", "")

# For SOURCE_TYPE="local": path to docs directory (e.g. /path/to/postgresql/docs).
LOCAL_DOCS_PATH = os.environ.get("KNOWLEDGE_LOCAL_DOCS_PATH", "")

# Relative path within repo (for git mode). Script searches docs/stable/sql or docs/sql.
DOCS_REL_PATHS = ["docs/stable/sql", "docs/sql", "doc/sql"]

OUTPUT_FILENAME = os.environ.get("KNOWLEDGE_OUTPUT_FILENAME", "extracted_knowledge.txt")
# Optional: full output path (overrides WORK_DIR + OUTPUT_FILENAME when set).
OUTPUT_PATH = os.environ.get("KNOWLEDGE_OUTPUT_PATH", "")

# Directory order for chunk numbering (adapt per source layout).
DIR_ORDER = [
    "introduction", "query_syntax", "statements", "functions",
    "data_types", "expressions", "aggregates", "configuration",
]


def setup_repository():
    """Prepare source: clone git repo or validate local path."""
    print("=" * 60)
    print("STEP 1: Preparing Documentation Source...")
    print(f"Target dialect: {TARGET_DIALECT}")
    print(f"Source type: {SOURCE_TYPE}")

    if SOURCE_TYPE == "local":
        if not LOCAL_DOCS_PATH or not os.path.isdir(LOCAL_DOCS_PATH):
            print(f"Error: LOCAL_DOCS_PATH must be an existing directory: {LOCAL_DOCS_PATH}")
            sys.exit(1)
        print(f"Using local docs: {LOCAL_DOCS_PATH}")
        return LOCAL_DOCS_PATH

    if SOURCE_TYPE != "git":
        print(f"Error: SOURCE_TYPE must be 'git' or 'local', got: {SOURCE_TYPE}")
        sys.exit(1)

    if not WORK_DIR:
        print("Error: WORK_DIR is required for git source.")
        sys.exit(1)
    os.makedirs(WORK_DIR, exist_ok=True)
    full_repo_path = os.path.join(WORK_DIR, LOCAL_REPO_NAME)

    if os.path.isdir(full_repo_path):
        print(f"Repository exists: {full_repo_path}")
    else:
        if not GIT_REPO_URL or not LOCAL_REPO_NAME:
            print("Error: GIT_REPO_URL and LOCAL_REPO_NAME required for git clone.")
            sys.exit(1)
        print(f"Cloning from {GIT_REPO_URL}...")
        try:
            subprocess.run(["git", "clone", GIT_REPO_URL, full_repo_path], check=True)
            print("Clone successful.")
        except subprocess.CalledProcessError:
            print("Error: Git clone failed.")
            sys.exit(1)

    for rel in DOCS_REL_PATHS:
        p = os.path.join(full_repo_path, rel)
        if os.path.isdir(p):
            print(f"Found docs at: {p}")
            return p

    if LOCAL_DOCS_PATH and os.path.isdir(LOCAL_DOCS_PATH):
        return LOCAL_DOCS_PATH

    print(f"Error: No docs folder found. Tried: {DOCS_REL_PATHS}")
    sys.exit(1)


class DocsExtractor:
    """Extract and format documentation from any dialect's official docs into @dialect2sql@ blocks."""

    def __init__(self, dialect_name: str, root_path: str, output_path: str, dir_order: list = None):
        self.dialect_name = dialect_name
        self.root_path = root_path
        self.output_path = output_path
        self.dir_order = dir_order or DIR_ORDER
        self.cat_counters = {d: i + 1 for i, d in enumerate(self.dir_order)}
        self.next_cat_id = len(self.dir_order) + 1

    def get_cat_id(self, dir_name: str) -> int:
        if dir_name not in self.cat_counters:
            self.cat_counters[dir_name] = self.next_cat_id
            self.next_cat_id += 1
        return self.cat_counters[dir_name]

    def clean_markdown_text(self, text: str) -> str:
        """Remove images, resolve links, strip HTML comments."""
        text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"<!--[\s\S]*?-->", "", text)
        return text.strip()

    def extract_content(self, file_path: str) -> list:
        """Extract content from a Markdown file (text + code segments)."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []

        content = re.sub(r"^---[\s\S]*?---\n", "", content)
        code_pattern = r"(```(?:sql)?[\s\S]*?```)"
        segments_raw = re.split(code_pattern, content, flags=re.IGNORECASE)

        segments = []
        for seg in segments_raw:
            if not seg.strip():
                continue
            if seg.strip().startswith("```"):
                m = re.search(r"```(?:sql)?([\s\S]*?)```", seg, re.IGNORECASE)
                if m:
                    segments.append({"type": "code", "content": m.group(1).strip()})
            else:
                clean = self.clean_markdown_text(seg)
                if clean:
                    segments.append({"type": "text", "content": clean})

        if segments:
            return [{"segments": segments}]
        return []

    def generate_block(self, item: dict, indices: tuple, names: tuple) -> str:
        """Format one doc block with @dialect2sql@ delimiters."""
        cat_id, file_id = indices
        cat_name, sub_cat_name = names
        full_index = f"{cat_id}.{file_id}"

        lines = ["@dialect2sql@", f"{full_index} {cat_name}: {sub_cat_name}", ""]
        lines.append("1. Official Documentation Content & Examples:")

        for seg in item["segments"]:
            if seg["type"] == "text":
                for line in seg["content"].split("\n"):
                    line = line.strip()
                    if line:
                        lines.append(f"   {line}")
                lines.append("")
            elif seg["type"] == "code":
                lines.append(f"   -- {self.dialect_name} Syntax Example")
                for c_line in seg["content"].split("\n"):
                    lines.append(f"   {c_line}")
                lines.append("")

        lines.append("@dialect2sql@\n")
        return "\n".join(lines)

    def run(self) -> None:
        """Scan root_path for .md files and write formatted output."""
        print("=" * 50)
        print(f"STEP 2: Scanning {self.root_path} for {self.dialect_name} docs...")

        results = []
        for root, dirs, files in os.walk(self.root_path):
            rel_path = os.path.relpath(root, self.root_path)
            if rel_path == ".":
                continue

            dir_name = rel_path.split(os.sep)[0]
            cat_id = self.get_cat_id(dir_name)
            cat_name = dir_name.replace("_", " ").title()
            file_counter = 1

            for f in sorted(files):
                if not f.endswith(".md"):
                    continue
                file_path = os.path.join(root, f)
                sub_cat_name = Path(f).stem.replace("_", " ").title()

                for item in self.extract_content(file_path):
                    block = self.generate_block(
                        item, (cat_id, file_counter), (cat_name, sub_cat_name)
                    )
                    results.append(block)
                file_counter += 1

        os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as out:
            out.write("\n".join(results))

        print(f"Processed {len(results)} blocks. Output: {self.output_path}")
        print("=" * 50)


def main():
    docs_path = setup_repository()
    if OUTPUT_PATH:
        output_path = OUTPUT_PATH
    elif WORK_DIR:
        output_path = os.path.join(WORK_DIR, OUTPUT_FILENAME)
    else:
        output_path = OUTPUT_FILENAME

    extractor = DocsExtractor(TARGET_DIALECT, docs_path, output_path, DIR_ORDER)
    extractor.run()


if __name__ == "__main__":
    main()
