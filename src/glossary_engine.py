import json
from pathlib import Path
from typing import Dict


def load_glossary(path: str) -> Dict[str, str]:
    """Load a JSON glossary file into a flat mapping.

    Expected format: a flat object mapping source_term -> preferred_target_term.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

    # If nested structures are present, flatten simply by merging string values.
    flat = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str):
                flat[k] = v
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, str):
                        flat[k2] = v2
    return flat


def build_glossary_instructions(glossary: Dict[str, str]) -> str:
    """Return a human-readable block to be embedded in system prompt instructing the model to use the glossary."""
    if not glossary:
        return "Nenhum glossário fornecido."
    lines = [f"{src} -> {tgt}" for src, tgt in glossary.items()]
    return "Use o glossário abaixo (não altere nomes/termos listados):\n" + "\n".join(lines)


def apply_glossary_postprocessing(text: str, glossary: Dict[str, str]) -> str:
    """Optional deterministic post-processing: replace occurrences using glossary where safe.

    This is conservative and literal; for advanced usage prefer model-guided application.
    """
    if not glossary:
        return text
    out = text
    for src, tgt in glossary.items():
        out = out.replace(src, tgt)
    return out


def ensure_novel_session(novel_name: str, base_dir: str = ".") -> str:
    """Ensure glossary/{novel_name}/ exists with `terms.json` and `context_memory.txt`.

    Returns the novel glossary dir path as string.
    """
    base = Path(base_dir)
    novel_dir = base / "glossary" / novel_name
    novel_dir.mkdir(parents=True, exist_ok=True)
    terms = novel_dir / "terms.json"
    context = novel_dir / "context_memory.txt"
    if not terms.exists():
        terms.write_text("{}", encoding="utf-8")
    if not context.exists():
        context.write_text("", encoding="utf-8")
    return str(novel_dir)


def load_terms_for_novel(novel_name: str, base_dir: str = ".") -> Dict[str, str]:
    p = Path(base_dir) / "glossary" / novel_name / "terms.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def append_context_memory(novel_name: str, text: str, base_dir: str = ".") -> None:
    p = Path(base_dir) / "glossary" / novel_name / "context_memory.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n\n")


def read_context_memory(novel_name: str, base_dir: str = ".") -> str:
    p = Path(base_dir) / "glossary" / novel_name / "context_memory.txt"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def load_suggestions(novel_name: str, base_dir: str = ".") -> list:
    """Load suggestion list from suggestions.json."""
    p = Path(base_dir) / "glossary" / novel_name / "suggestions.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def append_suggestion(novel_name: str, suggestion: str, base_dir: str = ".") -> None:
    """Append a suggestion to suggestions.json (avoid duplicates)."""
    p = Path(base_dir) / "glossary" / novel_name / "suggestions.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    suggestions = load_suggestions(novel_name, base_dir)
    if suggestion not in suggestions:
        suggestions.append(suggestion)
    p.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8")
