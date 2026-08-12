"""Validate required provenance and scope markers in migration documentation."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "docs" / "migrations" / "2026-08-12-operator-systems-template-into-operator-shared-core.md"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"

REQUIRED_MIGRATION_MARKERS = (
    "https://github.com/FishRaposo/operator-systems-template.git",
    "ac056271b0c7a9a92aa9430f5e1dc72fd8009f62",
    "Documentation-only absorption.",
    "## Source-path mapping",
    "## Explicitly excluded runtime paths",
    "## License and attribution",
    "MIT License",
    "## Archive gate",
    "Archive status: not approved",
)
REFERENCE_PATH = "docs/migrations/2026-08-12-operator-systems-template-into-operator-shared-core.md"


def missing_markers(path: Path, markers: tuple[str, ...]) -> list[str]:
    if not path.is_file():
        return [f"missing file: {path.relative_to(ROOT)}"]

    contents = path.read_text(encoding="utf-8")
    return [f"{path.relative_to(ROOT)} missing: {marker}" for marker in markers if marker not in contents]


def main() -> int:
    failures = missing_markers(MIGRATION, REQUIRED_MIGRATION_MARKERS)
    failures.extend(missing_markers(README, (REFERENCE_PATH,)))
    failures.extend(missing_markers(AGENTS, ("make check-migrations", REFERENCE_PATH)))

    if failures:
        print("Migration documentation check failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print("Migration documentation provenance check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
