thonimport json
import logging
from pathlib import Path
from typing import Any, Iterable, List

logger = logging.getLogger(__name__)

def export_to_json_file(records: Iterable[dict], path: Path) -> None:
    """
    Writes all records to a single JSON file as an array.

    The parent directory is created if it doesn't exist.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data: List[Any] = list(records)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Exported %d record(s) to %s", len(data), path)
    except Exception as exc:
        logger.exception("Failed to export records to %s: %s", path, exc)
        raise