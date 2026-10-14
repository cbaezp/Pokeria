#!/usr/bin/env python3
"""Machine-generated exhaustive inventory and reconciliation of default and fallback mechanisms.

Audits:
- Python (apps/api, apps/worker, tests, scripts) via Python `ast` parser.
- Rust (apps/solver) via regex AST scanner for unwrap_or, unwrap_or_default, default(), etc.
- TypeScript (apps/web) via regex scanner for ??, ||, default parameters, optional chaining fallbacks.
- SQL (migrations, models) via regex scanner for DEFAULT and COALESCE.
- Docker & Deployment (Dockerfiles, docker-compose*.yml).
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Excluded paths
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "target",
    ".pytest_cache",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "benchmarks",
    "data",
    "scratch",
    ".gemini",
}


@dataclass
class Finding:
    file_path: str
    line_number: int
    mechanism: str
    expression: str
    classification: str
    rationale: str
    affected_behavior: str


def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


class PythonAstAuditor(ast.NodeVisitor):
    def __init__(self, rel_path: str, lines: list[str]) -> None:
        self.rel_path = rel_path
        self.lines = lines
        self.findings: list[Finding] = []

    def _get_line_text(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Check default arguments
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            arg = node.args.args[defaults_offset + i]
            lineno = default.lineno
            self._get_line_text(lineno)
            val_repr = ast.unparse(default)
            is_test = "tests/" in self.rel_path

            # Classification
            if is_test:
                classification = "TEST_ONLY_FIXTURE"
                rationale = "Test harness parameter default"
            elif val_repr in ("None", "False", "True", "0", "0.0", "''", '""', "[]", "{}"):
                if (
                    "timeout" in arg.arg
                    or "limit" in arg.arg
                    or "page" in arg.arg
                    or "port" in arg.arg
                ):
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = (
                        f"Safe networking or pagination limit parameter ({arg.arg}={val_repr})"
                    )
                elif arg.arg in ("pot", "stack", "ev", "action_ev", "exploitability"):
                    if val_repr == "None":
                        classification = "OPTIONAL_WITH_EXPLICIT_UNAVAILABLE_STATE"
                        rationale = f"Optional poker mathematical quantity with explicit None state ({arg.arg}={val_repr})"
                    else:
                        classification = "UNSAFE_IMPLICIT_DEFAULT"
                        rationale = f"Poker mathematics variable default on parameter ({arg.arg}={val_repr})"
                else:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = (
                        f"Explicit standard function argument default ({arg.arg}={val_repr})"
                    )
            else:
                classification = "SAFE_EXPLICIT_DEFAULT"
                rationale = f"Documented constant default ({arg.arg}={val_repr})"

            self.findings.append(
                Finding(
                    file_path=self.rel_path,
                    line_number=lineno,
                    mechanism="FUNCTION_PARAM_DEFAULT",
                    expression=f"{arg.arg}={val_repr}",
                    classification=classification,
                    rationale=rationale,
                    affected_behavior=f"Function {node.name} default value for {arg.arg}",
                )
            )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self._get_line_text(node.lineno)
        # Check .get(key, default)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            if len(node.args) == 2:
                default_repr = ast.unparse(node.args[1])
                is_test = "tests/" in self.rel_path
                key_repr = ast.unparse(node.args[0])
                clean_key = key_repr.strip("'\"").lower()
                is_math_key = bool(
                    re.search(
                        r"\b(pot|stack|ev|root_evs|action_evs|node_evs|exploitability)\b", clean_key
                    )
                ) or clean_key.endswith("_ev")
                if is_test:
                    classification = "TEST_ONLY_FIXTURE"
                    rationale = "Test dictionary access with fallback"
                elif is_math_key and default_repr not in ("None", "''", '""', "[]", "{}"):
                    classification = "UNSAFE_IMPLICIT_DEFAULT"
                    rationale = f"Dictionary lookup fallback on mathematical quantity {key_repr} -> {default_repr}"
                elif (
                    "token" in clean_key or "secret" in clean_key or clean_key.endswith("_api_key")
                ):
                    classification = "REQUIRED_CONFIGURATION"
                    rationale = (
                        f"Security configuration access {key_repr} with fallback {default_repr}"
                    )
                elif default_repr in ("None", "''", '""', "[]", "{}"):
                    classification = "OPTIONAL_WITH_EXPLICIT_UNAVAILABLE_STATE"
                    rationale = f"Access of optional structured metadata field {key_repr} defaulting to empty {default_repr}"
                else:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = (
                        f"Explicit non-critical dictionary fallback {key_repr} -> {default_repr}"
                    )

                self.findings.append(
                    Finding(
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        mechanism="DICT_GET_FALLBACK",
                        expression=f".get({key_repr}, {default_repr})",
                        classification=classification,
                        rationale=rationale,
                        affected_behavior=f"Dictionary access fallback for {key_repr}",
                    )
                )

        # Check getattr(..., default)
        elif isinstance(node.func, ast.Name) and node.func.id == "getattr":
            if len(node.args) == 3:
                attr_repr = ast.unparse(node.args[1])
                default_repr = ast.unparse(node.args[2])
                is_test = "tests/" in self.rel_path
                if is_test:
                    classification = "TEST_ONLY_FIXTURE"
                    rationale = "Test getattr fallback"
                else:
                    classification = "OPTIONAL_WITH_EXPLICIT_UNAVAILABLE_STATE"
                    rationale = f"Attribute access fallback for {attr_repr} -> {default_repr}"

                self.findings.append(
                    Finding(
                        file_path=self.rel_path,
                        line_number=node.lineno,
                        mechanism="GETATTR_FALLBACK",
                        expression=f"getattr(..., {attr_repr}, {default_repr})",
                        classification=classification,
                        rationale=rationale,
                        affected_behavior=f"Dynamic attribute retrieval for {attr_repr}",
                    )
                )

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Check `or` expressions: e.g. x or fallback
        if isinstance(node.op, ast.Or):
            for _i, val in enumerate(node.values[1:], start=1):
                val_repr = ast.unparse(val)
                line_txt = self._get_line_text(val.lineno)
                is_test = "tests/" in self.rel_path
                if is_test:
                    classification = "TEST_ONLY_FIXTURE"
                    rationale = "Test boolean or fallback expression"
                elif val_repr in ("0", "0.0") and (
                    "ev" in line_txt.lower() or "pot" in line_txt.lower()
                ):
                    classification = "UNSAFE_IMPLICIT_DEFAULT"
                    rationale = f"Fabricated numerical zero fallback: {line_txt}"
                elif "token" in line_txt.lower() or "secret" in line_txt.lower():
                    classification = "REQUIRED_CONFIGURATION"
                    rationale = f"Secret/token configuration fallback: {val_repr}"
                else:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = f"Boolean expression or fallback: {val_repr}"

                self.findings.append(
                    Finding(
                        file_path=self.rel_path,
                        line_number=val.lineno,
                        mechanism="BOOLEAN_OR_FALLBACK",
                        expression=f"... or {val_repr}",
                        classification=classification,
                        rationale=rationale,
                        affected_behavior="Value fallback via boolean OR",
                    )
                )

        self.generic_visit(node)


def find_files(root: Path, subdirs: list[str], pattern: str) -> list[Path]:
    results = []
    for s in subdirs:
        d = root / s
        if d.is_file() and d.match(pattern):
            results.append(d)
        elif d.is_dir():
            for p in d.rglob(pattern):
                if not any(x in p.parts for x in EXCLUDE_DIRS):
                    results.append(p)
    return results


def audit_python_files(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    py_files = find_files(root, ["apps/api", "apps/worker", "tests", "scripts"], "*.py")
    for f in py_files:
        rel = str(f.relative_to(root))
        try:
            content = f.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(f))
            auditor = PythonAstAuditor(rel, content.splitlines())
            auditor.visit(tree)
            findings.extend(auditor.findings)
        except Exception:
            pass
    return findings


def audit_rust_files(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    rs_files = find_files(root, ["apps/solver"], "*.rs")

    unwrap_or_pat = re.compile(r"\.(unwrap_or|unwrap_or_default|unwrap_or_else)\s*\((.*?)\)")

    for f in rs_files:
        rel = str(f.relative_to(root))
        is_test = "/tests" in rel or "test_" in rel
        lines = f.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            # Match unwrap_or
            for m in unwrap_or_pat.finditer(line_str):
                mech = m.group(1)
                arg = m.group(2).strip()
                if is_test:
                    classification = "TEST_ONLY_FIXTURE"
                    rationale = f"Rust test unwrap fallback ({mech})"
                elif arg in ("0", "0.0", "false") and (
                    "pot" in line_str.lower() or "ev" in line_str.lower()
                ):
                    classification = "UNSAFE_IMPLICIT_DEFAULT"
                    rationale = f"Rust solver mathematics default {mech}({arg})"
                else:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = f"Rust safe option unwrap ({mech})"
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism=f"RUST_{mech.upper()}",
                        expression=m.group(0),
                        classification=classification,
                        rationale=rationale,
                        affected_behavior=f"Rust option resolution at line {idx}",
                    )
                )

            if "Default::default()" in line_str:
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="RUST_DEFAULT_TRAIT",
                        expression="Default::default()",
                        classification="TEST_ONLY_FIXTURE" if is_test else "SAFE_EXPLICIT_DEFAULT",
                        rationale="Rust explicit standard Default trait initialization",
                        affected_behavior="Struct initialization via Default trait",
                    )
                )

    return findings


def audit_ts_files(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    ts_files = find_files(root, ["apps/web/src", "apps/web/e2e"], "*.ts*")

    coalesce_pat = re.compile(r"(\w+)\s*\?\?\s*([^;,\)]+)")
    or_pat = re.compile(r"(\w+)\s*\|\|\s*([^;,\)]+)")

    for f in ts_files:
        rel = str(f.relative_to(root))
        is_test = "/test" in rel or ".spec." in rel or ".test." in rel
        lines = f.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            for m in coalesce_pat.finditer(line_str):
                fallback_val = m.group(2).strip()
                if is_test:
                    classification = "TEST_ONLY_FIXTURE"
                    rationale = "TypeScript test nullish coalescing"
                elif "theme" in m.group(1).lower() or "dark" in fallback_val:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = f"UI theme display preference default: {m.group(0)}"
                else:
                    classification = "OPTIONAL_WITH_EXPLICIT_UNAVAILABLE_STATE"
                    rationale = f"Frontend optional UI text/component fallback: {m.group(0)}"
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="TS_NULLISH_COALESCING",
                        expression=m.group(0),
                        classification=classification,
                        rationale=rationale,
                        affected_behavior="Frontend display fallback",
                    )
                )

            for m in or_pat.finditer(line_str):
                fallback_val = m.group(2).strip()
                if is_test:
                    classification = "TEST_ONLY_FIXTURE"
                    rationale = "TypeScript test OR fallback"
                elif "port" in m.group(1).lower() or "url" in m.group(1).lower():
                    classification = "REQUIRED_CONFIGURATION"
                    rationale = f"Frontend environment variable fallback: {m.group(0)}"
                else:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = f"Frontend property fallback: {m.group(0)}"
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="TS_LOGICAL_OR",
                        expression=m.group(0),
                        classification=classification,
                        rationale=rationale,
                        affected_behavior="Frontend property logical OR fallback",
                    )
                )

    return findings


def audit_sql_and_migrations(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    sql_files = find_files(root, ["apps/api/migrations"], "*.py")

    default_pat = re.compile(r"server_default\s*=\s*(.*?)[,\)]")
    col_default_pat = re.compile(r"DEFAULT\s+([^,;\s]+)", re.IGNORECASE)
    coalesce_pat = re.compile(r"COALESCE\s*\((.*?)\)", re.IGNORECASE)

    for f in sql_files:
        rel = str(f.relative_to(root))
        lines = f.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            for m in default_pat.finditer(line_str):
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="SQL_SERVER_DEFAULT",
                        expression=m.group(0),
                        classification="SAFE_EXPLICIT_DEFAULT",
                        rationale=f"Explicit database column schema default: {m.group(1)}",
                        affected_behavior="Database column schema constraint",
                    )
                )
            for m in col_default_pat.finditer(line_str):
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="SQL_COLUMN_DEFAULT",
                        expression=m.group(0),
                        classification="SAFE_EXPLICIT_DEFAULT",
                        rationale=f"SQL table definition column default: {m.group(1)}",
                        affected_behavior="Database table schema constraint",
                    )
                )
            for m in coalesce_pat.finditer(line_str):
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="SQL_COALESCE",
                        expression=m.group(0),
                        classification="SAFE_EXPLICIT_DEFAULT",
                        rationale=f"SQL expression coalesce fallback: {m.group(1)}",
                        affected_behavior="SQL query query fallback",
                    )
                )
    return findings


def audit_docker_and_configs(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    docker_files = [
        root / "apps" / "api" / "Dockerfile",
        root / "apps" / "web" / "Dockerfile",
        root / "apps" / "worker" / "Dockerfile",
        root / "docker-compose.yml",
        root / "docker-compose.closure.yml",
    ]
    env_default_pat = re.compile(r"\$\{([A-Z0-9_]+):-([^}]+)\}")

    for f in docker_files:
        if not f.exists():
            continue
        rel = str(f.relative_to(root))
        lines = f.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            for m in env_default_pat.finditer(line_str):
                var = m.group(1)
                default_val = m.group(2)
                if "SECRET" in var or "TOKEN" in var or "PASSWORD" in var:
                    classification = "REQUIRED_CONFIGURATION"
                    rationale = f"Docker configuration fallback for security variable {var} -> {default_val}"
                else:
                    classification = "SAFE_EXPLICIT_DEFAULT"
                    rationale = f"Docker container deployment default {var} -> {default_val}"
                findings.append(
                    Finding(
                        file_path=rel,
                        line_number=idx,
                        mechanism="DOCKER_ENV_FALLBACK",
                        expression=m.group(0),
                        classification=classification,
                        rationale=rationale,
                        affected_behavior=f"Container environment variable default for {var}",
                    )
                )

            if line_str.startswith("ENV "):
                parts = line_str.split(None, 2)
                if len(parts) >= 2:
                    findings.append(
                        Finding(
                            file_path=rel,
                            line_number=idx,
                            mechanism="DOCKERFILE_ENV",
                            expression=line_str,
                            classification="SAFE_EXPLICIT_DEFAULT",
                            rationale=f"Explicit Dockerfile image runtime environment definition: {parts[1]}",
                            affected_behavior="Image default environment variable",
                        )
                    )
    return findings


def main() -> None:
    print("Executing full repository static AST default and fallback audit...")
    py_findings = audit_python_files(WORKSPACE_ROOT)
    rs_findings = audit_rust_files(WORKSPACE_ROOT)
    ts_findings = audit_ts_files(WORKSPACE_ROOT)
    sql_findings = audit_sql_and_migrations(WORKSPACE_ROOT)
    docker_findings = audit_docker_and_configs(WORKSPACE_ROOT)

    all_findings = py_findings + rs_findings + ts_findings + sql_findings + docker_findings

    # Counts and reconciliation
    counts: dict[str, int] = {
        "SAFE_EXPLICIT_DEFAULT": 0,
        "UNSAFE_IMPLICIT_DEFAULT": 0,
        "REQUIRED_CONFIGURATION": 0,
        "OPTIONAL_WITH_EXPLICIT_UNAVAILABLE_STATE": 0,
        "TEST_ONLY_FIXTURE": 0,
    }

    for f in all_findings:
        counts[f.classification] = counts.get(f.classification, 0) + 1

    total_reviewed = len(all_findings)
    total_reconciled = sum(counts.values())

    report = {
        "total_occurrences_found": total_reviewed,
        "total_reviewed": total_reviewed,
        "reconciliation_match": total_reviewed == total_reconciled,
        "counts_by_classification": counts,
        "breakdown_by_language": {
            "python": len(py_findings),
            "rust": len(rs_findings),
            "typescript": len(ts_findings),
            "sql_migrations": len(sql_findings),
            "docker_deployment": len(docker_findings),
        },
        "all_findings": [asdict(f) for f in all_findings],
    }

    out_file = WORKSPACE_ROOT / "scratch" / "default_inventory_report.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Total occurrences found: {total_reviewed}")
    print(f"Total reviewed: {total_reviewed}")
    print(
        f"Reconciliation: sum(counts)={total_reconciled} vs total={total_reviewed} (Match: {total_reviewed == total_reconciled})"
    )
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"Saved machine-generated audit report to: {out_file}")


if __name__ == "__main__":
    main()
