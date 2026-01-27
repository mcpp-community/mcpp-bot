from pathlib import Path

def load_simple_yaml(path: str) -> dict:
    """
    Load a simple YAML file (supports basic key-value pairs and nested objects).

    Args:
        path: Path to the YAML file

    Returns:
        Dictionary representation of the YAML content
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = [ln.rstrip("\n") for ln in text.splitlines()]

    def parse_value(v: str):
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            if not inner:
                return []
            parts = [p.strip() for p in inner.split(",")]
            out = []
            for p in parts:
                if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                    out.append(p[1:-1])
                else:
                    out.append(p)
            return out
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]
        if v in ("true", "false"):
            return v == "true"
        return v

    root = {}
    stack = [(0, root)]
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.strip().startswith("#"):
            i += 1
            continue
        # Remove inline comments
        ln = ln.split("#")[0].rstrip()
        if not ln.strip():
            i += 1
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        key, _, val = ln.strip().partition(":")
        val = val.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]

        # Check for multiline string (| or >)
        if val == "|" or val == ">":
            # Literal block scalar (|) or folded block scalar (>)
            preserve_newlines = (val == "|")
            multiline_content = []
            i += 1
            # Find the base indentation of the multiline content
            base_indent = None
            while i < len(lines):
                next_ln = lines[i]
                # Skip empty lines
                if not next_ln.strip():
                    if base_indent is not None:
                        multiline_content.append("")
                    i += 1
                    continue
                # Check if this line is part of the multiline content
                next_indent = len(next_ln) - len(next_ln.lstrip(" "))
                if base_indent is None:
                    base_indent = next_indent
                if next_indent < indent + 2:
                    # This line is at the same or lower indentation, end of multiline
                    break
                # Add the line content (remove base indentation)
                content = next_ln[base_indent:] if len(next_ln) > base_indent else ""
                multiline_content.append(content.rstrip())
                i += 1
            # Join the lines
            if preserve_newlines:
                cur[key] = "\n".join(multiline_content)
            else:
                cur[key] = " ".join(multiline_content)
            continue
        elif val == "":
            cur[key] = {}
            stack.append((indent + 2, cur[key]))
        else:
            cur[key] = parse_value(val)
        i += 1
    return root
