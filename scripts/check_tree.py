"""Non-writing syntax/whitespace and protection inventory. Complete; do not change."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "tasks.json").read_text())
patterns = config["protected"]
required = ["README.md", "SPEC.md", "PROMPT.md", "tasks.json", ".gitignore", "LICENSE",
            "pll/__init__.py", "pll/_errors.py", "pll/_values.py", "tests/__init__.py", "pll/_rate.py", "pll/_span.py", "pll/_pacer.py",
            "pll/_follower_values.py"]
required += [str(p.relative_to(root)) for folder in ("scripts", "tests", "fixtures", "docs")
             for p in (root / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
required += [str(p.relative_to(root)) for p in [root / "README.md"] + list((root / "docs").rglob("README.md"))
             if not any(part in (".git", ".loop", ".wtha") for part in p.parts)]
for path in sorted(set(required)):
    matched = subprocess.run(["grep", "-E", "--", "|".join(patterns)], input=path + "\n",
                             text=True, capture_output=True).returncode == 0
    if not matched:
        raise SystemExit(f"unprotected contract path: {path}")
for folder in ("pll", "tests", "scripts"):
    for path in (root / folder).rglob("*.py"):
        text = path.read_text()
        compile(text, str(path), "exec")
        if not text.endswith("\n") or any(line != line.rstrip() for line in text.splitlines()):
            raise SystemExit(f"whitespace check failed: {path}")
print(f"PASS PROTECTIONS {len(set(required))}")
print("PASS SYNTAX AND WHITESPACE")
