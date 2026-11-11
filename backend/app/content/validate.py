"""CLI: python -m app.content.validate [dir] — used by CI gate `make content-validate`."""

import sys
from pathlib import Path

from app.content.repository import ContentRepository
from app.core.config import get_settings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else get_settings().content_dir
    repo = ContentRepository.from_dir(path)
    scenarios = repo.list()
    levels = sorted({s.cefr.value for s in scenarios})
    print(f"OK: {len(scenarios)} scenarios, levels={levels}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
