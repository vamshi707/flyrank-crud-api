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

## Real Run Report

```json
{
  "discovered_urls": 60,
  "unique_urls": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_page_count": 1
}


Save it.

Then:

```bash
git add scraper/README.md
git commit -m "A5: document real scraper run"
git push