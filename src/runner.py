thonimport argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

# Ensure src/ is on sys.path so we can import sibling modules even if executed from project root
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parent
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extractors.linkedin_job_parser import LinkedInJobParser, JobPosting  # type: ignore
from outputs.exporters import export_to_json_file  # type: ignore

DEFAULT_SETTINGS_PATH = SRC_DIR / "config" / "settings.example.json"
DEFAULT_INPUTS_PATH = PROJECT_ROOT / "data" / "inputs.sample.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "sample_output.json"

def configure_logging(level: str = "INFO") -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Advanced LinkedIn Job Scraper (No Cookies)"
    )
    parser.add_argument(
        "--settings",
        type=str,
        default=str(DEFAULT_SETTINGS_PATH),
        help="Path to settings JSON file.",
    )
    parser.add_argument(
        "--inputs",
        type=str,
        default=str(DEFAULT_INPUTS_PATH),
        help="Path to inputs JSON file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to output JSON file.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Override max worker threads (otherwise taken from settings).",
    )
    return parser

def run_scraper(
    settings: Dict[str, Any],
    inputs: Dict[str, Any],
    output_path: Path,
    max_workers_override: int | None = None,
) -> List[Dict[str, Any]]:
    logger = logging.getLogger("runner")
    scraper_settings = settings.get("scraper", {})
    max_workers = max_workers_override or scraper_settings.get("maxWorkers", 6)

    parser = LinkedInJobParser(settings=settings)

    searches = inputs.get("searches", [])
    if not isinstance(searches, list) or not searches:
        logger.warning("No searches defined in inputs file.")
        return []

    jobs: List[JobPosting] = []
    search_tasks = []
    logger.info("Starting %d search(es)...", len(searches))

    # First phase: search-level concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for search in searches:
            title = search.get("title", "")
            location = search.get("location", "")
            max_results = int(search.get("maxResults", scraper_settings.get("defaultMaxResults", 50)))
            filters = search.get("filters", {})
            if not title:
                logger.warning("Skipping search with empty title: %s", search)
                continue
            future = executor.submit(
                parser.search_jobs,
                query=title,
                location=location,
                max_results=max_results,
                filters=filters,
            )
            search_tasks.append(future)

        for future in as_completed(search_tasks):
            try:
                result_jobs = future.result()
                logger.info("Search returned %d job(s).", len(result_jobs))
                jobs.extend(result_jobs)
            except Exception as exc:
                logger.exception("Search task failed: %s", exc)

    logger.info("Collected %d job(s) from all searches. Fetching job details...", len(jobs))

    # Second phase: job-detail concurrency
    detailed_jobs: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(parser.fetch_job_details_safe, job.linkedin_url, job.to_dict()): job
            for job in jobs
        }

        for future in as_completed(futures):
            base_job = futures[future]
            try:
                detailed = future.result()
                detailed_jobs.append(detailed)
            except Exception as exc:
                logger.exception("Failed to enrich job %s: %s", base_job.id, exc)
                detailed_jobs.append(base_job.to_dict())

    logger.info("Fetched details for %d job(s).", len(detailed_jobs))

    # Persist results
    export_to_json_file(detailed_jobs, output_path)

    logger.info("Scraping completed. Output written to %s", output_path)
    return detailed_jobs

def main(argv: List[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    configure_logging()

    settings_path = Path(args.settings)
    inputs_path = Path(args.inputs)
    output_path = Path(args.output)

    if not settings_path.is_file():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    if not inputs_path.is_file():
        raise FileNotFoundError(f"Inputs file not found: {inputs_path}")

    settings = load_json(settings_path)
    inputs = load_json(inputs_path)

    os.makedirs(output_path.parent, exist_ok=True)

    run_scraper(
        settings=settings,
        inputs=inputs,
        output_path=output_path,
        max_workers_override=args.max_workers,
    )

if __name__ == "__main__":
    main()