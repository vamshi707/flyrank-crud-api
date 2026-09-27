import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from hashlib import md5

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, ValidationError


BASE_URL = "https://books.toscrape.com/"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/vamshi707/flyrank-crud-api)"
TIMEOUT = 10
DELAY = 0.5

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"
OUTPUT_DIR = ROOT / "output"

CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": USER_AGENT
}


class Book(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: str


stats = {
    "pages_fetched": 0,
    "cache_hits": 0
}


def cache_name(url):
    return md5(url.encode()).hexdigest() + ".html"


def fetch(url, cache_file=None, retry=True):

    if cache_file and cache_file.exists():
        stats["cache_hits"] += 1
        print("CACHE HIT:", url)

        return (
            cache_file.read_text(
                encoding="utf-8"
            ),
            True
        )

    print("FETCH:", url)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        if response.status_code != 200:

            if response.status_code >= 500 and retry:
                time.sleep(1)
                return fetch(
                    url,
                    cache_file,
                    retry=False
                )

            raise RuntimeError(
                f"HTTP {response.status_code}"
            )

        stats["pages_fetched"] += 1

        # Force UTF-8 so £ is decoded correctly
        html = response.content.decode(
            "utf-8"
        )

        if cache_file:
            cache_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            cache_file.write_text(
                html,
                encoding="utf-8"
            )

        time.sleep(DELAY)

        return html, False

    except requests.Timeout:

        if retry:
            time.sleep(1)

            return fetch(
                url,
                cache_file,
                retry=False
            )

        raise


def discover_books():

    all_urls = []
    page_url = BASE_URL

    for page_number in range(1, 4):

        cache_file = (
            CACHE_DIR
            / f"catalogue-page-{page_number}.html"
        )

        html, _ = fetch(
            page_url,
            cache_file
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for link in soup.select("h3 a"):

            href = link.get("href")

            book_url = urljoin(
                page_url,
                href
            )

            all_urls.append(book_url)

        next_link = soup.select_one(
            "li.next a"
        )

        if next_link:
            page_url = urljoin(
                page_url,
                next_link.get("href")
            )

    unique_urls = list(
        dict.fromkeys(all_urls)
    )

    print(
        f"catalogue_pages=3 "
        f"discovered={len(unique_urls)} "
        f"unique_urls={len(unique_urls)}"
    )

    return unique_urls


def parse_book(
    html,
    product_url,
    source_page
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    title_element = soup.select_one(
        "div.product_main h1"
    )

    price_element = soup.select_one(
        "div.product_main .price_color"
    )

    availability_element = soup.select_one(
        "div.product_main .availability"
    )

    rating_element = soup.select_one(
        "div.product_main p.star-rating"
    )

    description_element = soup.select_one(
        "#product_description + p"
    )

    if not title_element:
        raise ValueError("Missing title")

    if not price_element:
        raise ValueError("Missing price")

    if not availability_element:
        raise ValueError(
            "Missing availability"
        )

    title = title_element.get_text(
        strip=True
    )

    price_text = price_element.get_text(
        strip=True
    )

    price_gbp = float(
        price_text.replace("£", "")
    )

    availability_text = (
        availability_element
        .get_text(" ", strip=True)
    )

    rating_text = ""

    if rating_element:

        classes = rating_element.get(
            "class",
            []
        )

        rating_text = " ".join(
            item
            for item in classes
            if item != "star-rating"
        )

    description = None

    if description_element:

        description = (
            description_element
            .get_text(" ", strip=True)
        )

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "price_gbp": price_gbp,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(
            timezone.utc
        ).isoformat()
    }


def main():

    start_time = time.time()

    failed_pages = []
    records = []
    errors = []

    print("\n=== DISCOVERING BOOKS ===")

    book_urls = discover_books()

    test_urls = book_urls + [
        "https://books.toscrape.com/fake-book-for-testing/"
    ]

    print("\n=== FETCHING BOOK DETAILS ===")

    for index, url in enumerate(
        test_urls,
        start=1
    ):

        # Cache is based on URL, not number
        cache_file = (
            CACHE_DIR
            / "details"
            / cache_name(url)
        )

        try:

            html, _ = fetch(
                url,
                cache_file
            )

            source_page = (
                f"https://books.toscrape.com/"
                f"catalogue/page-"
                f"{((index - 1) // 20) + 1}.html"
            )

            raw_record = parse_book(
                html,
                url,
                source_page
            )

            try:

                book = Book.model_validate(
                    raw_record
                )

                records.append(
                    book.model_dump(
                        mode="json"
                    )
                )

            except ValidationError as error:

                errors.append({
                    "url": url,
                    "reason": str(error)
                })

        except Exception as error:

            print(
                "FAILED:",
                url,
                error
            )

            failed_pages.append({
                "url": url,
                "reason": str(error)
            })

    with (
        OUTPUT_DIR / "books.json"
    ).open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False
        )

    with (
        OUTPUT_DIR / "errors.json"
    ).open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            errors,
            file,
            indent=2,
            ensure_ascii=False
        )

    duration = round(
        time.time() - start_time,
        2
    )

    report = {
        "started_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "duration_seconds": duration,
        "catalogue_pages": 3,
        "discovered_urls": len(book_urls),
        "unique_urls": len(set(book_urls)),
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": len(records),
        "invalid_records": len(errors),
        "failed_pages": failed_pages,
        "failed_page_count": len(failed_pages)
    }

    with (
        OUTPUT_DIR / "run-report.json"
    ).open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\n=== FINAL REPORT ===")
    print("Books discovered:", len(book_urls))
    print("Valid records:", len(records))
    print("Invalid records:", len(errors))
    print("Failed pages:", len(failed_pages))
    print("Cache hits:", stats["cache_hits"])
    print("Duration:", duration, "seconds")


if __name__ == "__main__":
    main()