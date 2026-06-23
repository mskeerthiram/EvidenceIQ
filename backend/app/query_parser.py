"""
Query parser — extracts (category, location) from a natural query.

Starts simple on purpose: the "X in Y" pattern covers every example in
the brief exactly ("Cardiologists in Birmingham", "Plumbers in Houston").
If messier queries show up during testing, swap this for a single
small LLM call rather than growing a pile of regexes.
"""
import re

PATTERN = re.compile(r"^\s*(.+?)\s+in\s+(.+?)\s*$", re.IGNORECASE)


def parse_query(query: str) -> tuple[str, str]:
    match = PATTERN.match(query)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    # Fallback: no "in" found — treat the whole string as category, location unknown.
    return query.strip(), ""
