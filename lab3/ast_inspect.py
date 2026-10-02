import ast
from pathlib import Path

source = Path("vulnerable_app.py").read_text(encoding="utf-8")
tree = ast.parse(source)

print(ast.dump(tree, indent=2))

print("\nPotentially interesting calls:")

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            name = "<complex call>"
        print(f"line={getattr(node, 'lineno', '?')}: {name}")
