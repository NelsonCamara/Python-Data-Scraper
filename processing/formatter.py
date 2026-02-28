"""Format and clean raw scraped stats text files."""

import re
import logging

logger = logging.getLogger(__name__)


def format_stats_file(input_path, output_path):
    """Clean raw stats: remove units, normalize whitespace, add pipe delimiters.

    Args:
        input_path: Path to the raw stats text file.
        output_path: Path to write the formatted output.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    formatted_lines = []
    for line in lines:
        line = line.replace("yrs", "").replace("cm", "")
        line = " ".join(line.split())
        formatted_lines.append(line)

    content = "\n".join(formatted_lines)

    # Add pipe delimiter between concatenated words (e.g. "GroundDuels" -> "Ground|Duels")
    content = re.sub(r"([a-z])([A-Z])", r"\1|\2", content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Formatted %d lines: %s -> %s", len(formatted_lines), input_path, output_path)
