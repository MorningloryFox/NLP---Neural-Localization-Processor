import re


def format_text(text: str, japanese_mode: bool = False) -> str:
    """Apply formatting rules:
    - If japanese_mode: replace straight quotes with 「 and 」
    - Else: use em-dash — for dialogue (replace leading quotes with em-dash)
    - Remove excessive blank lines (more than one)
    """
    out = text

    # Normalize line endings
    out = out.replace("\r\n", "\n").replace("\r", "\n")

    if japanese_mode:
        # Replace ASCII double quotes around dialogue with Japanese quotes
        out = re.sub(r'"(.*?)"', lambda m: f'「{m.group(1)}」', out, flags=re.S)
    else:
        # Replace lines starting with "- " or leading quotes with em-dash
        out = re.sub(r'^[ \t]*[-–—]\s*', '— ', out, flags=re.M)
        out = re.sub(r'^\s*"', '— ', out, flags=re.M)

    # Collapse more than 2 newlines into two newlines (single blank line between paragraphs)
    out = re.sub(r"\n{3,}", "\n\n", out)

    # Trim trailing spaces on lines
    out = "\n".join([ln.rstrip() for ln in out.splitlines()])

    return out.strip() + "\n"
