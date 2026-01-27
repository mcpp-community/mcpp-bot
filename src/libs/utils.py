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
    for ln in lines:
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        # Remove inline comments
        ln = ln.split("#")[0].rstrip()
        if not ln.strip():
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        key, _, val = ln.strip().partition(":")
        val = val.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]
        if val == "":
            cur[key] = {}
            stack.append((indent + 2, cur[key]))
        else:
            cur[key] = parse_value(val)
    return root
