"""Shared helpers for the business true/false quiz bank."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
INDEX_FILE = ROOT / "index" / "questions.json"
COVERAGE_FILE = ROOT / "coverage" / "coverage.json"
DEFAULT_SOURCE_REPO = "john1hsu/business-knowledge-graph"
DEFAULT_SOURCE_DIR = ROOT / ".source" / "business-knowledge-graph"
# The source repo publishes every article as a readable web page.
SITE_URL = "https://john1hsu.github.io/business-knowledge-graph"

ID_RE = re.compile(r"^bz-\d{6}$")
KT_RE = re.compile(r"^kt:[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
YEAR_RE = re.compile(r"\b(1[89]|20)\d{2}\b")

STATUSES = ("active", "stale", "retired")
# What a pair teaches, so practice can cover each side of a topic and you can drill one kind.
KINDS = {
    "definition": "What it is",
    "origin": "Who and when",
    "mechanism": "How it works",
    "evidence": "Evidence and critiques",
    "application": "In practice",
    "figure": "Numbers and dates",
}

REQUIRED = (
    "id", "area", "kind", "topic", "true_statement", "false_statement", "explanation",
    "source", "concepts", "difficulty", "created", "status",
)
OPTIONAL = ("topic_type", "as_of", "related", "supersedes", "stale_reason", "retired_reason")
FIELD_ORDER = ("id", "area", "kind", "topic", "topic_type", "true_statement", "false_statement",
               "explanation", "as_of", "source", "concepts", "related", "supersedes", "difficulty",
               "created", "status", "stale_reason", "retired_reason")


def question_files() -> list[Path]:
    return sorted(QUESTIONS_DIR.glob("*/bz-*.yaml"))


def load_question(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    for key in ("created", "as_of"):
        if key in data and data[key] is not None and not isinstance(data[key], str):
            data[key] = str(data[key])
    return data


def load_all() -> list[tuple[Path, dict]]:
    return [(p, load_question(p)) for p in question_files()]


def ordered(record: dict) -> dict:
    out = {k: record[k] for k in FIELD_ORDER if k in record and record[k] not in (None, [], "")}
    for k, v in record.items():  # keep anything unexpected so validation can flag it
        if k not in out and k not in FIELD_ORDER:
            out[k] = v
    return out


def dump_question(record: dict) -> str:
    return yaml.safe_dump(ordered(record), sort_keys=False, allow_unicode=True, width=10_000)


def save_question(record: dict) -> Path:
    path = QUESTIONS_DIR / record["area"] / f"{record['id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_question(record), encoding="utf-8")
    return path


def find_question(qid: str) -> tuple[Path, dict]:
    for path in QUESTIONS_DIR.glob(f"*/{qid}.yaml"):
        return path, load_question(path)
    sys.exit(f"no question with id {qid}")


def next_id() -> str:
    nums = [int(p.stem[3:]) for p in QUESTIONS_DIR.glob("*/bz-*.yaml") if ID_RE.match(p.stem)]
    return f"bz-{(max(nums) + 1 if nums else 1):06d}"


def article_slug(path: str) -> str:
    return Path(path).stem


def article_url(src: dict) -> str:
    """The readable web page for the source article (phone-friendly)."""
    return f"{SITE_URL}/articles/{article_slug(src['path'])}.html"


def source_url(src: dict) -> str:
    return f"https://github.com/{src['repo']}/blob/main/{src['path']}"


# ---------- source repo (business-knowledge-graph) ----------

def git(src_dir: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(src_dir), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def source_head(src_dir: Path) -> str:
    return git(src_dir, "rev-parse", "HEAD")


def source_blob(src_dir: Path, rel_path: str) -> str | None:
    try:
        return git(src_dir, "rev-parse", f"HEAD:{rel_path}")
    except subprocess.CalledProcessError:
        return None


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


def load_articles(src_dir: Path) -> dict[str, dict]:
    """Map article path -> metadata, from the source repo's articles/ folder."""
    out = {}
    for path in sorted((src_dir / "articles").glob("*/*.md")):
        fm = read_frontmatter(path)
        rel = path.relative_to(src_dir).as_posix()
        relations = [r for r in fm.get("relations") or [] if isinstance(r, dict)]
        neighbors = [*(fm.get("broader") or []), *(fm.get("related") or []),
                     *(r.get("object") for r in relations)]
        out[rel] = {
            "path": rel,
            "id": fm.get("id"),
            "title": fm.get("title"),
            "type": fm.get("type"),
            "domain": fm.get("domain"),
            "summary": " ".join(str(fm.get("summary") or "").split()),
            "created": str(fm.get("created", "")),
            # every node this article has an edge to, in order, without repeats
            "neighbors": list(dict.fromkeys(n for n in neighbors if isinstance(n, str) and n != fm.get("id"))),
        }
    return out


def resolve_source_dir(arg: str | None) -> Path:
    path = Path(arg) if arg else DEFAULT_SOURCE_DIR
    if not (path / "articles").is_dir():
        sys.exit(f"source repo not found at {path}; clone {DEFAULT_SOURCE_REPO} there or pass --source")
    return path


def print_json(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))
