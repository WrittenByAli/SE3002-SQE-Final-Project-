#!/usr/bin/env python3
"""Keep Cosmic Ray work items inside the confirmed BR1–BR4 function list."""

import ast
import sys
from pathlib import Path

import yaml
from cosmic_ray.work_db import WorkDB, use_db


ROOT = Path(__file__).resolve().parents[3]
SCOPE = ROOT / "tests/team/rule_surface.yml"


def target_ranges():
    scope = yaml.safe_load(SCOPE.read_text())
    targets = {}
    for item in scope["functions"]:
        path = item["file"]
        module = ast.parse((ROOT / path).read_text())
        wanted_class = item["class"]
        wanted_function = item["function"]

        def visit(nodes, class_name=None):
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    if visit(node.body, node.name):
                        return True
                elif (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and node.name == wanted_function and class_name == wanted_class):
                    targets.setdefault(path, []).append((node.lineno, node.end_lineno))
                    return True
            return False

        if not visit(module.body):
            raise RuntimeError(f"Could not resolve scoped function {wanted_class}.{wanted_function} in {path}")
    return targets


def main(session_path):
    root = ROOT.resolve()
    targets = target_ranges()
    with use_db(session_path, WorkDB.Mode.open) as db:
        selected = []
        for item in db.work_items:
            if len(item.mutations) != 1:
                continue
            mutation = item.mutations[0]
            path = Path(mutation.module_path)
            try:
                relative = str(path.resolve().relative_to(root))
            except ValueError:
                relative = mutation.module_path
            line = mutation.start_pos[0]
            if any(start <= line <= end for start, end in targets.get(relative, ())):
                selected.append(item)
        if not selected:
            raise RuntimeError("Scope filter selected zero mutations; refusing an empty campaign")
        db.clear()
        db.add_work_items(selected)
        print(f"Scoped Cosmic Ray session to {len(selected)} mutations in {len(targets)} rule-surface files")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} SESSION.sqlite")
    main(sys.argv[1])
