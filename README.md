# Task 1: LinkedIn Profile Scraper

## Setup

1. Install dependencies:
pip install -r requirements.txt

2. Download ChromeDriver or use webdriver-manager
3. Update credentials in scraper.py (EMAIL and PASSWORD)

## Usage

python scraper.py

## Features
- Automated login to LinkedIn
- Anti-detection measures (random user agents, delays)
- Scrapes: name, headline, location, about, company, connections
- Saves data to CSV file
- Handles 20 sample profiles

## Tips
- Use a test LinkedIn account
- Add delays between requests
- Consider using proxies for large-scale scraping
- LinkedIn may require CAPTCHA solving
