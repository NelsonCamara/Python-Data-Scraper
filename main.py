"""SofaScore Football Player Stats Scraper - Main entry point.

Usage:
    python main.py collect-links       Collect player profile URLs from league pages
    python main.py scrape-stats        Scrape stats for all collected players
    python main.py rescrape            Re-scrape players that failed or are missing
    python main.py format              Format raw stats file (clean units, add delimiters)
    python main.py export              Parse formatted stats and export to Excel
    python main.py pipeline            Run the full pipeline: collect -> scrape -> format -> export
"""

import argparse
import logging
import os

from config import (
    OUTPUT_DIR,
    PLAYER_LINKS_FILE,
    PLAYER_STATS_FILE,
    PLAYER_STATS_FORMATTED_FILE,
    EXCEL_OUTPUT_FILE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def cmd_collect_links(args):
    """Collect player links from SofaScore league pages."""
    from scraper.browser import create_driver
    from scraper.player_scraper import collect_player_links, save_player_links

    ensure_output_dir()
    driver = create_driver(headless=args.headless)
    try:
        players = collect_player_links(driver)
        save_player_links(players)
    finally:
        driver.quit()


def cmd_scrape_stats(args):
    """Scrape individual player stats from their profile pages."""
    from scraper.browser import create_driver
    from scraper.player_scraper import scrape_all_player_stats

    ensure_output_dir()
    driver = create_driver(headless=args.headless)
    try:
        scrape_all_player_stats(driver, start_index=args.start)
    finally:
        driver.quit()


def cmd_rescrape(args):
    """Re-scrape specific players by name search."""
    from scraper.browser import create_driver
    from scraper.search_scraper import rescrape_players
    from processing.deduplicator import find_missing_scrapes

    ensure_output_dir()

    if args.names:
        player_names = args.names
    else:
        missing_urls = find_missing_scrapes(PLAYER_LINKS_FILE, PLAYER_STATS_FILE)
        player_names = [url.split("/")[4] for url in missing_urls]

    if not player_names:
        logger.info("No players to re-scrape.")
        return

    logger.info("Re-scraping %d players", len(player_names))
    output_file = os.path.join(OUTPUT_DIR, "rescrape_stats.txt")
    driver = create_driver(headless=args.headless)
    try:
        rescrape_players(driver, player_names, output_file=output_file)
    finally:
        driver.quit()


def cmd_format(args):
    """Format raw stats file: remove units, normalize whitespace."""
    from processing.formatter import format_stats_file

    input_file = args.input or PLAYER_STATS_FILE
    output_file = args.output or PLAYER_STATS_FORMATTED_FILE
    format_stats_file(input_file, output_file)


def cmd_export(args):
    """Parse formatted stats and export to Excel."""
    from processing.parser import parse_stats_file, remove_duplicates, export_to_excel

    input_file = args.input or PLAYER_STATS_FORMATTED_FILE
    output_file = args.output or EXCEL_OUTPUT_FILE

    players = parse_stats_file(input_file)
    players = remove_duplicates(players)
    export_to_excel(players, output_file)


def cmd_pipeline(args):
    """Run the full pipeline: collect links, scrape stats, format, export."""
    logger.info("=== Starting full pipeline ===")

    logger.info("--- Step 1/4: Collecting player links ---")
    cmd_collect_links(args)

    logger.info("--- Step 2/4: Scraping player stats ---")
    args.start = 0
    cmd_scrape_stats(args)

    logger.info("--- Step 3/4: Formatting stats ---")
    args.input = None
    args.output = None
    cmd_format(args)

    logger.info("--- Step 4/4: Exporting to Excel ---")
    args.input = None
    args.output = None
    cmd_export(args)

    logger.info("=== Pipeline complete ===")


def main():
    parser = argparse.ArgumentParser(
        description="SofaScore Football Player Stats Scraper",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run browser in headless mode (no GUI)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # collect-links
    subparsers.add_parser("collect-links", help="Collect player URLs from league pages")

    # scrape-stats
    sp_scrape = subparsers.add_parser("scrape-stats", help="Scrape stats for collected players")
    sp_scrape.add_argument("--start", type=int, default=0, help="Index to resume from")

    # rescrape
    sp_rescrape = subparsers.add_parser("rescrape", help="Re-scrape missing players")
    sp_rescrape.add_argument("--names", nargs="+", help="Specific player slugs to re-scrape")

    # format
    sp_format = subparsers.add_parser("format", help="Format raw stats file")
    sp_format.add_argument("--input", help="Input stats file path")
    sp_format.add_argument("--output", help="Output formatted file path")

    # export
    sp_export = subparsers.add_parser("export", help="Parse stats and export to Excel")
    sp_export.add_argument("--input", help="Input formatted stats file path")
    sp_export.add_argument("--output", help="Output Excel file path")

    # pipeline
    subparsers.add_parser("pipeline", help="Run the full pipeline")

    args = parser.parse_args()

    commands = {
        "collect-links": cmd_collect_links,
        "scrape-stats": cmd_scrape_stats,
        "rescrape": cmd_rescrape,
        "format": cmd_format,
        "export": cmd_export,
        "pipeline": cmd_pipeline,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
