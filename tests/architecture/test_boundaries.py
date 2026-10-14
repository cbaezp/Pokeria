"""Automated architectural dependency boundary tests.

Uses Python AST parsing to enforce strict Clean Architecture boundaries:
- Domain layer MUST NOT import from infrastructure, presentation, FastAPI, or SQLAlchemy.
- Application layer MUST NOT import from infrastructure, presentation, FastAPI, or SQLAlchemy.
- Presentation routes MUST NOT perform direct database queries or import ORM models.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
API_APP_DIR = REPO_ROOT / "apps" / "api" / "app"


def get_imports_from_file(file_path: Path) -> list[str]:
    """Parse a python file and return all imported module names."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def test_domain_layer_dependencies() -> None:
    """Domain layer must have ZERO dependencies on infrastructure, presentation, or external frameworks."""
    forbidden_modules = [
        "app.infrastructure",
        "app.presentation",
        "fastapi",
        "starlette",
        "sqlalchemy",
        "alembic",
    ]

    domain_dir = API_APP_DIR / "domain"
    python_files = list(domain_dir.rglob("*.py"))
    assert len(python_files) > 0, "No domain files found to check"

    violations: list[str] = []
    for py_file in python_files:
        imports = get_imports_from_file(py_file)
        for imp in imports:
            for forbidden in forbidden_modules:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)} imports '{imp}'")

    assert not violations, "Domain architectural boundary violations found:\n" + "\n".join(
        violations
    )


def test_application_layer_dependencies() -> None:
    """Application layer must NOT depend on concrete infrastructure or presentation layers."""
    forbidden_modules = [
        "app.infrastructure",
        "app.presentation",
        "fastapi",
        "starlette",
        "sqlalchemy",
        "alembic",
    ]

    app_dir = API_APP_DIR / "application"
    python_files = list(app_dir.rglob("*.py"))
    assert len(python_files) > 0, "No application files found to check"

    violations: list[str] = []
    for py_file in python_files:
        imports = get_imports_from_file(py_file)
        for imp in imports:
            for forbidden in forbidden_modules:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)} imports '{imp}'")

    assert not violations, "Application boundary violations found:\n" + "\n".join(violations)


def test_presentation_routes_do_not_import_database_models() -> None:
    """Presentation API routes must communicate via use cases, not direct ORM models."""
    routes_dir = API_APP_DIR / "presentation" / "api"
    python_files = list(routes_dir.rglob("*.py"))

    forbidden_modules = [
        "app.infrastructure.database.models",
    ]

    violations: list[str] = []
    for py_file in python_files:
        imports = get_imports_from_file(py_file)
        for imp in imports:
            for forbidden in forbidden_modules:
                if imp == forbidden or imp.startswith(f"{forbidden}."):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)} imports '{imp}'")

    assert not violations, "Presentation layer violations found:\n" + "\n".join(violations)
