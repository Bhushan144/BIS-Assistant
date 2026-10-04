import re

def clean_text(text: str) -> str:
    """
    Clean raw PDF text while preserving technical values, clause numbers, 
    units, standard numbers, lists, and tables.

    Rules:
    - Normalizes non-breaking spaces and control characters (like \\x0c form feed).
    - Removes repeated blank lines (>2 line breaks reduced to 2 line breaks).
    - Removes excessive trailing spaces on lines.
    - Preserves structural line breaks for clauses, list items, and table rows.
    """
    if not text:
        return ""

    # 1. Normalize special characters & form feeds
    text = text.replace("\x0c", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]", " ", text)
    text = re.sub(r"[\xA0\u1680\u180e\u2000-\u200b\u202f\u205f\u3000]", " ", text)  # Unicode spaces

    # 2. Trim trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # 3. Carefully join broken sentences across lines, but preserve headings, clauses, lists, tables
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if line should be preserved as standalone (heading, clause, bullet, table line, empty line)
        if not line.strip():
            cleaned_lines.append("")
            i += 1
            continue

        # Lookahead: if current line doesn't end with sentence terminator (. ! ? : ;)
        # and next line starts with lowercase or continuation, join them
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Don't join if next line looks like a new clause/heading, list item, or empty line
            is_next_clause = bool(re.match(r"^(?:IS|\d+[\.\d]*|[A-Z]\.\d*|Annex|Table|Figure|\-|\•|\*)\s", next_line, re.IGNORECASE))
            if next_line and not is_next_clause and not line.endswith((".", ":", ";", "!", "?")):
                # Join with space
                line = line + " " + next_line
                i += 1  # Skip next_line as it's merged

        cleaned_lines.append(line)
        i += 1

    # 4. Collapse 3+ consecutive newlines into double newline (paragraph break)
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    # 5. Remove multiple consecutive spaces within lines
    result = re.sub(r"[ ]{2,}", " ", result)

    return result.strip()
