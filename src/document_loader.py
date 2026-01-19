from pathlib import Path
import chardet
from typing import Optional, Tuple
import re

__all__ = [
    "read_text_file",
    "read_all_inputs",
    "normalize_stylistic_abbreviations",
    "normalize_chapter_titles",
]


def read_text_file(path: str, fallback_encoding: str = "utf-8") -> str:
    """Read a .txt file robustly, trying to detect encoding and falling back as needed.

    Returns the entire file content as a string.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    raw = p.read_bytes()
    # Try detection
    try:
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or fallback_encoding
    except Exception:
        encoding = fallback_encoding

    try:
        return raw.decode(encoding)
    except Exception:
        return raw.decode(fallback_encoding, errors="replace")


def read_all_inputs(input_dir: str) -> dict:
    """Read all .txt files from a folder, return mapping filename -> content."""
    p = Path(input_dir)
    items = {}
    if not p.exists():
        return items
    for f in p.glob("*.txt"):
        items[f.name] = read_text_file(str(f))
    return items

def normalize_stylistic_abbreviations(text: str) -> str:
    """Restaura abreviações estilísticas ou ofuscações (ex: 'leetspeak') para a grafia convencional.
    
    Isso garante que o modelo de linguagem processe a semântica correta em vez de
    tratar os termos como ruído ou dados desconhecidos.
    """
    # Use case-insensitive, whole-word boundary replacements
    replacements = [
        (r'\bv4g(?:1|i)?na\b', 'vagina'),
        (r'\bp3n(?:1|i)?s\b', 'pênis'),
        (r'\bc0ck\b', 'cock'),
        (r'\bp0rn\b', 'porn'),
        (r'\bsex0\b', 'sexo'),
        (r'\bm0an\b', 'moan'),
        (r'\bn(?:1|i)pp(?:le)?\b', 'nipple'),
        (r'\bor9asim\b', 'orgasm'),
    ]
    
    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def normalize_chapter_titles(text: str) -> tuple:
    """
    Normaliza títulos de capítulos.
    
    Retorna: (texto_limpo, titulo_detectado)
    Padrão esperado: "Capítulo X - Título longo" ou "Volume X, Chapter Y"
    
    Normaliza para: "Capítulo X" e remove do corpo do texto.
    """
    # Padrões para detectar títulos
    # Pattern 1: "Chapter 1 - Title" or "Capítulo 1 - Título"
    pattern1 = r'^(?:Chapter|Capítulo|Cap\.?)\s*([IVXivx\d]+)\s*[-:]*\s*(.+?)$'
    
    # Pattern 2: "Volume X, Chapter Y - Title"
    pattern2 = r'^(?:Volume|Vol\.?)\s*[\d]+\s*,?\s*(?:Chapter|Capítulo|Cap\.?)\s*[\d]+\s*[-:]*\s*(.+?)$'
    
    detected_title = ""
    clean_lines = []
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check for title pattern on first few lines only
        if i < 3 and stripped:
            match1 = re.match(pattern1, stripped, re.IGNORECASE)
            match2 = re.match(pattern2, stripped, re.IGNORECASE)
            
            if match1 and not detected_title:
                detected_title = match1.group(2).strip() if match1.lastindex >= 2 else stripped
                continue  # Skip this line
            elif match2 and not detected_title:
                detected_title = match2.group(1).strip()
                continue  # Skip this line
        
        clean_lines.append(line)
    
    clean_text = '\n'.join(clean_lines).strip()
    return (clean_text, detected_title)