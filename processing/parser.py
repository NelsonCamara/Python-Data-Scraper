"""Parse formatted stats text into structured data and export to Excel."""

import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

POSITION_CODES = {"GK", "DF", "MF", "FW", "DR", "DL", "DC", "MR", "ML", "MC", "AM", "DM", "ST", "RW", "LW"}
NON_POSITION_UPPER = {"FC", "FK", "AS", "A", "SK"}


def _is_position(word, index):
    """Check if a word is a position abbreviation."""
    if len(word) > 2 or index <= 3:
        return False
    return word.isupper() and 1 <= len(word) <= 2 and word not in NON_POSITION_UPPER


def _find_first_position_index(tokens):
    """Find the index of the first position token in the line."""
    for i, token in enumerate(tokens):
        if _is_position(token, i):
            return i
    return None


def _parse_strengths_weaknesses(tokens):
    """Extract strengths and weaknesses from the tokens after market value.

    Returns:
        Tuple of (strengths_list, weaknesses_list).
    """
    combined = []
    started = False
    for token in tokens:
        if started:
            combined.append(token)
        if "M€" in token or "K€" in token:
            started = True

    if combined:
        combined.pop()  # Remove preferred foot (last element)

    if not combined:
        return ["No outstanding strengths"], ["No outstanding weaknesses"]

    # Split by pipe delimiter and reconstruct multi-word items
    forces = []
    faiblesses = []

    # Find where strengths end and weaknesses begin
    full_text = " ".join(combined)
    parts = [p.strip() for p in re.split(r"\|", full_text) if p.strip()]

    # The transition point is where "No outstanding" appears or where
    # the text naturally splits between strengths and weaknesses sections
    strengths_items = []
    weaknesses_items = []

    found_weakness_marker = False
    for part in parts:
        if "No outstanding weakness" in part:
            weaknesses_items = ["No outstanding weaknesses"]
            found_weakness_marker = True
        elif "No outstanding strength" in part:
            strengths_items = ["No outstanding strengths"]
        elif found_weakness_marker:
            weaknesses_items.append(part)
        else:
            strengths_items.append(part)

    if not strengths_items:
        strengths_items = ["No outstanding strengths"]
    if not weaknesses_items:
        weaknesses_items = ["No outstanding weaknesses"]

    return strengths_items, weaknesses_items


def parse_stats_file(input_path):
    """Parse a formatted stats text file into a list of player dicts.

    Args:
        input_path: Path to the formatted stats text file.

    Returns:
        List of player stat dictionaries.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    players = []

    for line_num, line in enumerate(lines, 1):
        tokens = line.split()
        if len(tokens) < 10:
            logger.warning("Line %d too short, skipping", line_num)
            continue

        player = {}

        # Name from slug
        name_parts = tokens[0].split("-")
        player["Prenom"] = name_parts[0] if name_parts else ""
        player["Nom"] = "-".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Find nationality (3-letter uppercase code)
        nat_index = None
        for i, token in enumerate(tokens[1:], 1):
            if len(token) == 3 and token.isupper() and token[0].isalpha():
                player["Nationalite"] = token
                nat_index = i
                break

        if nat_index is None:
            logger.warning("Line %d: no nationality found, skipping", line_num)
            continue

        # Championship (between slug and nationality)
        player["Championnat"] = " ".join(tokens[1:nat_index])

        # Find positions
        pos_start = _find_first_position_index(tokens)
        if pos_start is None:
            logger.warning("Line %d: no position found, skipping", line_num)
            continue

        # Club (between nationality and first position)
        player["Club"] = " ".join(tokens[nat_index + 1 : pos_start])

        # Collect positions
        positions = []
        pos_end = pos_start
        for i in range(pos_start, len(tokens)):
            if _is_position(tokens[i], i):
                positions.append(tokens[i])
                pos_end = i
            else:
                break
        player["Postes"] = positions

        # After positions: age, height, 5 stats, value, strengths, weaknesses, foot
        data_start = pos_end + 1
        remaining = tokens[data_start:]

        if len(remaining) < 8:
            logger.warning("Line %d: insufficient stats data, skipping", line_num)
            continue

        player["Age"] = remaining[0]
        player["Taille"] = remaining[1]

        is_gk = positions[0] == "GK"
        if is_gk:
            player["Saves"] = remaining[2]
            player["Anticipation"] = remaining[3]
            player["Tactique Goal"] = remaining[4]
            player["Distribution du ballon"] = remaining[5]
            player["Jeu aerien"] = remaining[6]
        else:
            player["Attaque"] = remaining[2]
            player["Creativite"] = remaining[3]
            player["Technique"] = remaining[4]
            player["Defense"] = remaining[5]
            player["Tactique"] = remaining[6]

        player["Valeur"] = remaining[7]

        # Strengths & weaknesses
        strengths, weaknesses = _parse_strengths_weaknesses(tokens)
        player["Forces"] = strengths
        player["Faiblesses"] = weaknesses

        # Preferred foot (last token)
        player["Droitier Gaucher ou Ambi"] = tokens[-1]

        players.append(player)

    logger.info("Parsed %d players from %s", len(players), input_path)
    return players


def remove_duplicates(players):
    """Remove duplicate players based on name, age, height, and club."""
    seen = set()
    unique = []
    for p in players:
        key = (p.get("Prenom"), p.get("Nom"), p.get("Age"), p.get("Taille"), p.get("Club"))
        if key not in seen:
            seen.add(key)
            unique.append(p)
    logger.info("Removed %d duplicates (%d -> %d)", len(players) - len(unique), len(players), len(unique))
    return unique


def export_to_excel(players, output_path):
    """Export player data to an Excel file.

    Args:
        players: List of player stat dicts.
        output_path: Path for the output .xlsx file.
    """
    df = pd.DataFrame(players)
    df.to_excel(output_path, index=False)
    logger.info("Exported %d players to %s", len(players), output_path)
