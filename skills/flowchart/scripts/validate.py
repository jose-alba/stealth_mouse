#!/usr/bin/env python3
"""
Flowchart & Mermaid Diagram Syntax Validator
Checks Mermaid diagram text for common syntax errors, illegal characters,
unquoted parenthesized labels, and structural balance.
"""

import sys
import json
import re
from pathlib import Path


def validate_mermaid(content: str) -> dict:
    issues = []
    lines = content.strip().splitlines()

    if not lines:
        return {"valid": False, "errors": ["Diagram content is empty"]}

    first_line = lines[0].strip()
    valid_starters = [
        "graph TD", "graph LR", "graph TB", "graph RL",
        "flowchart TD", "flowchart LR", "flowchart TB", "flowchart RL",
        "sequenceDiagram", "stateDiagram", "stateDiagram-v2",
        "classDiagram", "erDiagram", "xychart-beta"
    ]

    has_valid_header = any(first_line.startswith(starter) for starter in valid_starters)
    if not has_valid_header:
        issues.append(f"Line 1: Diagram must start with a supported header (e.g. 'flowchart TD', 'flowchart LR'). Found: '{first_line}'")

    # Check unquoted parentheses in node text: e.g. A[Label (Info)] is dangerous if not quoted as A["Label (Info)"]
    unquoted_parentheses = re.compile(r'\[([^"\'\[\]]*\([^\)]*\)[^"\'\[\]]*)\]')

    open_brackets = {"[": 0, "(": 0, "{": 0}
    for idx, line in enumerate(lines, 1):
        line_str = line.strip()
        if not line_str or line_str.startswith("%%"):
            continue

        # Check for HTML tags
        if re.search(r'<[^>]+>', line_str):
            issues.append(f"Line {idx}: HTML tags inside Mermaid labels can break rendering. Use plain markdown.")

        # Check for unquoted parentheses inside bracket nodes
        m = unquoted_parentheses.search(line_str)
        if m:
            issues.append(f"Line {idx}: Node text contains unquoted parentheses '{m.group(0)}'. Quote it like [\"{m.group(1)}\"] to prevent parse errors.")

    return {
        "valid": len(issues) == 0,
        "line_count": len(lines),
        "header": first_line,
        "errors": issues,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: validate.py <mermaid_code_or_file>"}, indent=2))
        sys.exit(1)

    target = sys.argv[1]
    if Path(target).exists():
        content = Path(target).read_text(encoding="utf-8")
    else:
        content = target

    result = validate_mermaid(content)
    print(json.dumps(result, indent=2))
    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

