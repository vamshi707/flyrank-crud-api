# The Polite Scraper

## Target classification

Target: Books to Scrape

Books to Scrape is a public practice sandbox created for learning web scraping.

Scope: The first 3 catalogue pages only, containing 60 books.

Data collected:

- title
- product_url
- price_text
- price_gbp
- availability_text
- rating_text
- description
- source_page
- fetched_at

Robots check: no robots file found.

I will not reuse this code on another site without checking its rules and terms first.

## Python lane

This project uses:

- Python 3.10+
- Requests
- Beautiful Soup
- Pydantic
- JSON

## Installation

From the repository root:

```bash
pip install -r scraper/requirements.txt