"""Re-scrape specific players by searching them on SofaScore."""

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from scraper.player_scraper import (
    dismiss_cookie_popup,
    scrape_player_stats,
    save_player_stats,
)

logger = logging.getLogger(__name__)


def search_and_scrape_player(driver, player_name, is_first=False, output_file=None):
    """Search for a player by name on SofaScore and scrape their stats.

    Args:
        driver: Selenium WebDriver instance.
        player_name: Player slug (e.g. 'david-raya').
        is_first: If True, navigate to sofascore.com first and dismiss popups.
        output_file: Path to save stats.
    """
    search_name = player_name.replace("-", " ")

    if is_first:
        driver.get("https://www.sofascore.com/")
        dismiss_cookie_popup(driver)

    # Find and use the search box
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'header input[type="text"], header form input')
            )
        )
        search_box = driver.find_element(
            By.CSS_SELECTOR, 'header input[type="text"], header form input'
        )
    except TimeoutException:
        logger.error("Could not find search box for player: %s", player_name)
        return

    search_box.clear()
    search_box.send_keys(search_name)

    # Click the first search result
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "header a[href*='/player/']"))
        )
        result_link = driver.find_element(By.CSS_SELECTOR, "header a[href*='/player/']")
        player_url = result_link.get_attribute("href")
    except TimeoutException:
        logger.warning("No search results found for: %s", player_name)
        return

    stats = scrape_player_stats(driver, player_url)
    if stats:
        save_player_stats(stats, filepath=output_file)
        logger.info("Re-scraped: %s", player_name)
    else:
        logger.warning("Could not scrape stats for: %s", player_name)


def rescrape_players(driver, player_names, output_file=None):
    """Re-scrape a list of players by searching their names.

    Args:
        driver: Selenium WebDriver instance.
        player_names: List of player slugs (e.g. ['david-raya', 'nick-pope']).
        output_file: Path to save stats.
    """
    for i, name in enumerate(player_names):
        logger.info("[%d/%d] Searching: %s", i + 1, len(player_names), name)
        search_and_scrape_player(driver, name, is_first=(i == 0), output_file=output_file)
