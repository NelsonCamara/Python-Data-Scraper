import os
from dotenv import load_dotenv

load_dotenv()

SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY", "")

# Leagues to scrape: (name, url, max_pages)
LEAGUES = [
    ("Premier League", "https://www.sofascore.com/tournament/football/england/premier-league/17", 46),
    ("La Liga", "https://www.sofascore.com/tournament/football/spain/laliga/8", 35),
    ("Bundesliga", "https://www.sofascore.com/tournament/football/germany/bundesliga/35", 37),
    ("Serie A", "https://www.sofascore.com/tournament/football/italy/serie-a/23", 28),
    ("Ligue 1", "https://www.sofascore.com/tournament/football/france/ligue-1/34", 30),
    ("Liga Portugal", "https://www.sofascore.com/tournament/football/portugal/liga-portugal/238", 26),
    ("Eredivisie", "https://www.sofascore.com/tournament/football/netherlands/eredivisie/37", 26),
    ("Champions League", "https://www.sofascore.com/tournament/football/europe/uefa-champions-league/7", 29),
    ("Europa League", "https://www.sofascore.com/tournament/football/europe/uefa-europa-league/679", 30),
]

# Output paths (relative to project root)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
PLAYER_LINKS_FILE = os.path.join(OUTPUT_DIR, "player_links.txt")
PLAYER_STATS_FILE = os.path.join(OUTPUT_DIR, "player_stats.txt")
PLAYER_STATS_FORMATTED_FILE = os.path.join(OUTPUT_DIR, "player_stats_formatted.txt")
EXCEL_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sofascore_stats.xlsx")

# Browser settings
WINDOW_SIZE = "1920,1080"
