"""Scrape player links and statistics from SofaScore tournament pages."""

import time
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

from config import LEAGUES, PLAYER_LINKS_FILE, PLAYER_STATS_FILE

logger = logging.getLogger(__name__)


def dismiss_cookie_popup(driver):
    """Dismiss the SofaScore cookie/consent popup if present."""
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[4]/div[2]/div[1]/div[2]/div[2]/button[1]/p')
            )
        )
        popup_btn = driver.find_element(
            By.XPATH, '/html/body/div[4]/div[2]/div[1]/div[2]/div[2]/button[1]/p'
        )
        popup_btn.click()
    except TimeoutException:
        pass


def collect_player_links(driver, leagues=None):
    """Navigate tournament pages and collect all player profile URLs.

    Args:
        driver: Selenium WebDriver instance.
        leagues: List of (name, url, max_pages) tuples. Defaults to config.LEAGUES.

    Returns:
        List of unique player profile URLs.
    """
    if leagues is None:
        leagues = LEAGUES

    actions = ActionChains(driver)
    players = []

    for league_name, league_url, max_pages in leagues:
        logger.info("Scraping league: %s (%d pages)", league_name, max_pages)
        driver.get(league_url)
        dismiss_cookie_popup(driver)
        driver.execute_script("window.scrollTo(0, 4200);")

        for page_num in range(max_pages):
            time.sleep(10)
            try:
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[class="sc-75bb9fa3-8 kqAUgC"]')
                    )
                )
                tbody = table.find_element(By.CSS_SELECTOR, "tbody")
                for row in tbody.find_elements(By.CSS_SELECTOR, "tr"):
                    link_elem = row.find_elements(By.CSS_SELECTOR, "a")[1]
                    href = link_elem.get_attribute("href")
                    if href and href not in players:
                        players.append(href)
            except TimeoutException:
                logger.warning("Timeout on page %d of %s", page_num + 1, league_name)
                continue

            logger.info("  Page %d/%d - Total players: %d", page_num + 1, max_pages, len(players))

            # Click next page (except on the last page)
            if page_num < max_pages - 1:
                try:
                    nav_buttons = driver.find_elements(
                        By.CSS_SELECTOR, '[class="sc-bcXHqe iaTYZY"]'
                    )
                    WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable(nav_buttons[1])
                    )
                    actions.move_to_element(nav_buttons[1]).click().perform()
                except (IndexError, TimeoutException):
                    logger.warning("Could not navigate to next page")
                    break

    logger.info("Total unique players collected: %d", len(players))
    return players


def save_player_links(players, filepath=None):
    """Save player links to a text file, one URL per line."""
    if filepath is None:
        filepath = PLAYER_LINKS_FILE
    with open(filepath, "a", encoding="utf-8") as f:
        for url in players:
            f.write(url + "\n")
    logger.info("Saved %d player links to %s", len(players), filepath)


def _extract_value(raw_text):
    """Extract market value from raw HTML text (e.g., '€12.5M' -> '125M€')."""
    allowed = set("0123456789MK€.")
    return "".join(c for c in raw_text if c in allowed)


def _find_element_text(driver, css_selector, timeout=2):
    """Wait for and return the innerHTML of an element, or None on timeout."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        elem = driver.find_element(By.CSS_SELECTOR, css_selector)
        return elem.get_attribute("innerHTML")
    except (TimeoutException, NoSuchElementException):
        return None


def _extract_strengths_weaknesses(driver):
    """Extract player strengths and weaknesses from the profile page.

    Returns:
        Tuple of (strengths_str, weaknesses_str).
    """
    strengths = "No outstanding strengths"
    weaknesses = "No outstanding weaknesses"

    # Strengths
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[class*="eVoGht"] > div:nth-child(1)')
            )
        )
        container = driver.find_element(
            By.CSS_SELECTOR, '[class*="eVoGht"] > div:nth-child(1)'
        )
        spans = container.find_elements(By.CSS_SELECTOR, "div span")
        if spans:
            strengths = "|".join(s.get_attribute("innerHTML") for s in spans)
    except (TimeoutException, NoSuchElementException):
        pass

    # Weaknesses
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[class*="eVoGht"] > div:nth-child(2)')
            )
        )
        container = driver.find_element(
            By.CSS_SELECTOR, '[class*="eVoGht"] > div:nth-child(2)'
        )
        spans = container.find_elements(By.CSS_SELECTOR, "div span")
        if spans:
            weaknesses = "|".join(s.get_attribute("innerHTML") for s in spans)
    except (TimeoutException, NoSuchElementException):
        pass

    return strengths, weaknesses


def scrape_player_stats(driver, player_url, is_first=False):
    """Scrape a single player's statistics from their SofaScore profile.

    Args:
        driver: Selenium WebDriver instance.
        player_url: Full URL to the player's SofaScore profile.
        is_first: Whether this is the first player (to dismiss popup).

    Returns:
        A dict with the player's stats, or None if the player is inactive/missing data.
    """
    driver.get(player_url)
    slug = player_url.split("/")[4]
    logger.debug("Scraping player: %s", slug)

    if is_first:
        dismiss_cookie_popup(driver)

    stats = {"slug": slug}

    # Name
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div h2")
            )
        )
        name_elem = driver.find_element(By.CSS_SELECTOR, "div h2")
        name_parts = name_elem.get_attribute("innerHTML").split()
        stats["first_name"] = name_parts[0]
        stats["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        stats["first_name"] = slug
        stats["last_name"] = ""

    # Nationality (3-letter code) - quick check to see if player has enough data
    nationality_selectors = [
        '[class*="hjyjyy"] > div > span',
        '[class*="eqlBbO"] > div > span',
    ]
    nationality = None
    for sel in nationality_selectors:
        nationality = _find_element_text(driver, sel, timeout=3)
        if nationality:
            break
    if not nationality:
        logger.debug("Skipping %s - no nationality/insufficient data", slug)
        return None
    stats["nationality"] = nationality

    # Championship
    champ_selectors = [
        '[class*="cfIQRT"] > div',
        'ul > li:nth-child(3) > a',
    ]
    for sel in champ_selectors:
        champ = _find_element_text(driver, sel, timeout=3)
        if champ:
            stats["league"] = champ
            break
    else:
        logger.debug("Skipping %s - no league data", slug)
        return None

    # Club
    club_selectors = [
        '[class*="cyDYHi"]',
        '[class*="hPJQwa"]',
    ]
    for sel in club_selectors:
        club = _find_element_text(driver, sel, timeout=3)
        if club:
            stats["club"] = club
            break
    else:
        stats["club"] = "Unknown"

    # Age & Height
    stats["age"] = _find_element_text(driver, '[class*="hjyjyy"]', timeout=5) or ""
    stats["height"] = ""
    try:
        info_divs = driver.find_elements(By.CSS_SELECTOR, '[class*="hjyjyy"]')
        if len(info_divs) >= 2:
            stats["height"] = info_divs[1].get_attribute("innerHTML")
    except (NoSuchElementException, IndexError):
        pass

    # Positions
    positions = []
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '[class*="sc-f11cf694-0"]')
            )
        )
        pos_elems = driver.find_elements(By.CSS_SELECTOR, '[class*="sc-f11cf694-0"]')
        for elem in pos_elems:
            text_elem = elem.find_element(By.CSS_SELECTOR, "text")
            positions.append(text_elem.get_attribute("innerHTML"))
        positions = list(set(positions))
    except TimeoutException:
        pass
    if not positions:
        logger.debug("Skipping %s - no position data", slug)
        return None
    stats["positions"] = positions

    # Performance attributes (GK vs. outfield)
    is_goalkeeper = positions[0] == "GK"
    if is_goalkeeper:
        attr_map = {
            "saves": "saves",
            "anticipation": "anticipation",
            "tactical": "tactical",
            "ballDistribution": "ball_distribution",
            "aerial": "aerial",
        }
    else:
        attr_map = {
            "attacking": "attacking",
            "creativity": "creativity",
            "technical": "technical",
            "defending": "defending",
            "tactical": "tactical",
        }

    for css_class, key in attr_map.items():
        val = _find_element_text(driver, f".{css_class} > div > div > div", timeout=3)
        if val is None and key in ("saves", "attacking"):
            logger.debug("Skipping %s - no performance graph", slug)
            return None
        stats[key] = val or ""

    # Market value
    value_text = _find_element_text(driver, '[class*="gsYByW"], [class*="gNcBWu"]', timeout=5)
    stats["market_value"] = _extract_value(value_text) if value_text else ""

    # Strengths & Weaknesses
    strengths, weaknesses = _extract_strengths_weaknesses(driver)
    stats["strengths"] = strengths
    stats["weaknesses"] = weaknesses

    # Preferred foot
    foot_selectors = [
        '[class*="hjyjyy"]',
        '[class*="eqlBbO"]',
    ]
    try:
        info_divs = driver.find_elements(By.CSS_SELECTOR, foot_selectors[0])
        if len(info_divs) >= 4:
            stats["preferred_foot"] = info_divs[3].get_attribute("innerHTML")
        else:
            stats["preferred_foot"] = ""
    except (NoSuchElementException, IndexError):
        stats["preferred_foot"] = ""

    return stats


def save_player_stats(stats, filepath=None):
    """Append a single player's stats as a text line to the output file."""
    if filepath is None:
        filepath = PLAYER_STATS_FILE
    if stats is None:
        return

    is_gk = "saves" in stats
    positions_str = " ".join(stats["positions"])

    if is_gk:
        line = (
            f"{stats['slug']} {stats['league']} {stats['nationality']} "
            f"{stats['club']} {positions_str} {stats['age']} {stats['height']} "
            f"{stats['saves']} {stats['anticipation']} {stats['tactical']} "
            f"{stats['ball_distribution']} {stats['aerial']} "
            f"{stats['market_value']} {stats['strengths']} {stats['weaknesses']} "
            f"{stats['preferred_foot']}"
        )
    else:
        line = (
            f"{stats['slug']} {stats['league']} {stats['nationality']} "
            f"{stats['club']} {positions_str} {stats['age']} {stats['height']} "
            f"{stats['attacking']} {stats['creativity']} {stats['technical']} "
            f"{stats['defending']} {stats['tactical']} "
            f"{stats['market_value']} {stats['strengths']} {stats['weaknesses']} "
            f"{stats['preferred_foot']}"
        )

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def scrape_all_player_stats(driver, links_file=None, stats_file=None, start_index=0):
    """Iterate through a file of player links and scrape each player's stats.

    Args:
        driver: Selenium WebDriver instance.
        links_file: Path to the file containing player URLs.
        stats_file: Path to the output stats file.
        start_index: Index to resume scraping from.
    """
    if links_file is None:
        links_file = PLAYER_LINKS_FILE

    with open(links_file, "r", encoding="utf-8") as f:
        player_urls = [line.strip() for line in f if line.strip()]

    logger.info("Scraping stats for %d players (starting at index %d)", len(player_urls), start_index)

    for i in range(start_index, len(player_urls)):
        stats = scrape_player_stats(driver, player_urls[i], is_first=(i == start_index))
        if stats:
            save_player_stats(stats, filepath=stats_file)
            logger.info("[%d/%d] Scraped: %s", i + 1, len(player_urls), stats["slug"])
        else:
            logger.info("[%d/%d] Skipped: %s", i + 1, len(player_urls), player_urls[i].split("/")[4])
