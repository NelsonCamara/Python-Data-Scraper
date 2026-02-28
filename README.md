# SofaScore Football Player Stats Scraper

Web scraper that collects football player statistics from [SofaScore](https://www.sofascore.com), covering major European leagues.

## Data Collected

For each player, the scraper extracts:

| Field | Description |
|-------|-------------|
| Name | First and last name |
| Nationality | 3-letter country code |
| League | Championship name |
| Club | Current club |
| Positions | GK, DF, MF, FW, etc. |
| Age | Player age |
| Height | In centimeters |
| Performance | 5 attributes (varies by position) |
| Market Value | Estimated value in EUR |
| Strengths | Notable qualities |
| Weaknesses | Areas to improve |
| Preferred Foot | Left / Right / Ambidextrous |

**Outfield players**: Attacking, Creativity, Technical, Defending, Tactical

**Goalkeepers**: Saves, Anticipation, Tactical, Ball Distribution, Aerial

## Leagues Covered

Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Liga Portugal, Eredivisie, Champions League, Europa League.

## Setup

### Prerequisites

- Python 3.8+
- Google Chrome installed

### Installation

```bash
cd SofaScoreScraper
pip install -r requirements.txt
```

### Configuration

Copy the environment template and add your ScrapeOps API key (optional, for user-agent rotation):

```bash
cp .env.example .env
```

Edit `.env`:
```
SCRAPEOPS_API_KEY=your_key_here
```

Leagues and output paths can be adjusted in `config.py`.

## Usage

The scraper is controlled via CLI commands:

```bash
# 1. Collect player profile URLs from league pages
python main.py collect-links

# 2. Scrape individual player statistics
python main.py scrape-stats

# 3. Format raw stats (clean units, normalize)
python main.py format

# 4. Parse and export to Excel
python main.py export

# Or run the full pipeline at once
python main.py pipeline
```

### Options

```bash
# Run browser in headless mode (no GUI)
python main.py --headless collect-links

# Resume scraping from a specific index
python main.py scrape-stats --start 500

# Re-scrape specific players that failed
python main.py rescrape --names david-raya nick-pope

# Auto-detect and re-scrape all missing players
python main.py rescrape
```

## Project Structure

```
SofaScoreScraper/
├── main.py                  # CLI entry point
├── config.py                # Configuration (leagues, paths, settings)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
├── scraper/
│   ├── browser.py           # WebDriver setup & user-agent rotation
│   ├── player_scraper.py    # Player links & stats scraping
│   └── search_scraper.py    # Search-based re-scraping
├── processing/
│   ├── formatter.py         # Raw text cleaning & formatting
│   ├── parser.py            # Text-to-structured-data parsing & Excel export
│   └── deduplicator.py      # Duplicate detection & missing scrape finder
└── output/                  # Generated data files (git-ignored)
```

## How It Works

1. **Link Collection**: Navigates league standings pages on SofaScore, iterating through paginated tables to collect all player profile URLs.

2. **Stats Scraping**: Visits each player profile and extracts biographical info, performance ratings, market value, and strengths/weaknesses using Selenium.

3. **Formatting**: Cleans raw text output by removing units (`yrs`, `cm`), normalizing whitespace, and adding delimiters between concatenated words.

4. **Parsing & Export**: Converts the formatted text into structured dictionaries, removes duplicates, and exports to Excel.

## Disclaimer

This project is for educational purposes only. Respect SofaScore's terms of service and robots.txt. Use responsibly and avoid excessive request rates.
