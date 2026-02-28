"""Utilities for deduplicating player links and identifying failed scrapes."""

import logging

logger = logging.getLogger(__name__)


def deduplicate_links(input_path, output_path):
    """Remove duplicate URLs from a links file.

    Args:
        input_path: Path to the input links file.
        output_path: Path for the deduplicated output.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(unique)

    logger.info(
        "Deduplicated links: %d -> %d (%s)",
        len(lines), len(unique), output_path,
    )


def find_missing_scrapes(links_path, stats_path):
    """Compare scraped links with stats to find players that failed to scrape.

    Args:
        links_path: Path to the player links file.
        stats_path: Path to the player stats file.

    Returns:
        List of player URLs that have no corresponding stats.
    """
    with open(links_path, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    with open(stats_path, "r", encoding="utf-8") as f:
        stats_lines = f.readlines()

    scraped_slugs = set()
    for line in stats_lines:
        tokens = line.split()
        if tokens:
            scraped_slugs.add(tokens[0])

    missing = []
    for link in links:
        slug = link.split("/")[4] if len(link.split("/")) > 4 else ""
        if slug and slug not in scraped_slugs:
            missing.append(link)

    logger.info("Found %d missing scrapes out of %d links", len(missing), len(links))
    return missing
