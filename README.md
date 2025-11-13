# OSU Dining Menu Scraper

This tool fetches and searches dining menus from Oregon State University's Jamix API.  
It allows you to:

- Select a day of the week (or all days).
- Fetch menus for all dining locations.
- Search for menu items by keyword.
- Display item names and ingredient lists, grouped by location and day.

## Requirements

Make sure you have **Python 3.9+** installed.  
Then install the required packages:

```bash
pip install requests beautifulsoup4 lxml
```

## Usage

```bash
python menu.py
```

You will be prompted to choose to search the menus for a day of the week, or all days of the week.
You will also be prompted to enter a search term.
