"""Browser setup and user-agent rotation utilities."""

import requests
from random import choice
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import SCRAPEOPS_API_KEY, WINDOW_SIZE


def get_user_agent_list():
    """Fetch a list of user agents from ScrapeOps API."""
    if not SCRAPEOPS_API_KEY:
        return []
    response = requests.get(
        "http://headers.scrapeops.io/v1/user-agents",
        params={"api_key": SCRAPEOPS_API_KEY},
    )
    return response.json().get("result", [])


def get_random_user_agent(user_agent_list):
    """Pick a random user agent from the list."""
    if not user_agent_list:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    return choice(user_agent_list)


def create_driver(headless=False):
    """Create and configure a Selenium Chrome WebDriver.

    Args:
        headless: Run browser without GUI if True.

    Returns:
        A configured Chrome WebDriver instance.
    """
    options = Options()
    options.page_load_strategy = "none"
    options.add_argument(f"--window-size={WINDOW_SIZE}")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.set_capability("acceptInsecureCerts", True)

    if headless:
        options.add_argument("--headless")

    user_agents = get_user_agent_list()
    user_agent = get_random_user_agent(user_agents)
    options.add_argument(f"--user-agent={user_agent}")

    return webdriver.Chrome(options=options)
