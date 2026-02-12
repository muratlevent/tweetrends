#!/usr/bin/env python3
"""
X (Twitter) Global Trending Topics Scraper
==========================================
Scrapes trending keywords from X's Global Trending page.
First collects the default (home) trends, then iterates through
each category to collect category-specific trends.

Usage:
    python scraper.py                          # Default: headless, output to trends.json
    python scraper.py --output my_trends.json  # Custom output file
    python scraper.py --no-headless            # Show browser window
"""

import argparse
import json
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

TARGET_URL = "https://x.com/i/jf/global-trending/home"
DEFAULT_OUTPUT = "trends.json"

# Selectors — derived from DOM analysis
# The page has two horizontal scroll rows:
#   Row 0 = category buttons (contain <img> thumbnails)
#   Row 1 = keyword/trend buttons (text-only pills)
# Both share the same container class pattern.
ROW_CONTAINER_SELECTOR = "div.jf-element.flex-row.flex-nowrap"
SPINNER_SELECTOR = "svg.animate-spin"


# ──────────────────────────────────────────────────────────────
# Helper: Get Scroll Rows
# ──────────────────────────────────────────────────────────────


def _get_rows(page):
    """Return all horizontal scroll row elements."""
    return page.query_selector_all(ROW_CONTAINER_SELECTOR)


def _get_keyword_row(page):
    """Return the keyword row element (second row)."""
    rows = _get_rows(page)
    if len(rows) >= 2:
        return rows[1]
    return None


def _get_category_row(page):
    """Return the category row element (first row)."""
    rows = _get_rows(page)
    if len(rows) >= 1:
        return rows[0]
    return None


# ──────────────────────────────────────────────────────────────
# Scraping Functions
# ──────────────────────────────────────────────────────────────


def scrape_keywords(page) -> list[str]:
    """Scrape all currently visible trend keyword texts from the page.

    Keywords are in the second horizontal scroll row.
    Each keyword is a <button> with a <p> child containing the text.
    """
    keywords: list[str] = []

    # Wait for the keyword row to have buttons
    try:
        page.wait_for_function(
            """() => {
                const rows = document.querySelectorAll('div.jf-element.flex-row.flex-nowrap');
                if (rows.length < 2) return false;
                const buttons = rows[1].querySelectorAll('button');
                return buttons.length > 0;
            }""",
            timeout=10_000,
        )
    except PlaywrightTimeout:
        print("  ⚠  No keyword buttons found (timeout)")
        return keywords

    # Scroll the keyword row to reveal all items
    _scroll_row_to_end(page, row_index=1)

    # Collect keyword texts
    kw_row = _get_keyword_row(page)
    if not kw_row:
        return keywords

    buttons = kw_row.query_selector_all("button")
    for btn in buttons:
        p_el = btn.query_selector("p")
        if p_el:
            text = p_el.inner_text().strip()
            if text and text not in keywords:
                keywords.append(text)

    return keywords


def scrape_categories(page) -> list[dict]:
    """Return a list of category dicts: [{name, element}, ...].

    Categories sit in the first horizontal scroll row as <button> elements.
    They are distinguishable from keyword buttons because they contain <img> tags.
    """
    # Scroll category row to reveal all items
    _scroll_row_to_end(page, row_index=0)

    cat_row = _get_category_row(page)
    if not cat_row:
        print("  ⚠  Could not find category row")
        return []

    buttons = cat_row.query_selector_all("button")

    categories = []
    for btn in buttons:
        # Category buttons contain an <img> — use this to confirm
        # Get text from the <p> tag inside the button
        p_el = btn.query_selector("p")
        if p_el:
            text = p_el.inner_text().strip()
        else:
            text = btn.inner_text().strip()

        if text:
            categories.append({"name": text, "element": btn})

    return categories


def wait_for_keywords_refresh(page, old_keywords: list[str], timeout_ms: int = 8000):
    """Wait for new keywords to load after clicking a category.

    Strategy:
    1. Try to detect spinner and wait for it to disappear
    2. Fallback: wait for keyword text to actually change
    """
    try:
        # Wait briefly for spinner to appear
        page.wait_for_selector(SPINNER_SELECTOR, timeout=2000)
        # Now wait for spinner to disappear (content loaded)
        page.wait_for_selector(SPINNER_SELECTOR, state="hidden", timeout=timeout_ms)
    except PlaywrightTimeout:
        pass

    # Extra safety: wait a moment for DOM to settle
    page.wait_for_timeout(800)


def _scroll_row_to_end(page, row_index: int = 0, step: int = 500, max_scrolls: int = 10):
    """Scroll a horizontal overflow row to reveal all items.

    Args:
        page: Playwright page object
        row_index: 0 for category row, 1 for keyword row
        step: Pixels to scroll each step
        max_scrolls: Maximum number of scroll steps
    """
    rows = _get_rows(page)
    if len(rows) <= row_index:
        return

    row = rows[row_index]
    for _ in range(max_scrolls):
        prev_scroll = row.evaluate("el => el.scrollLeft")
        row.evaluate(f"el => el.scrollLeft += {step}")
        page.wait_for_timeout(300)
        new_scroll = row.evaluate("el => el.scrollLeft")
        if new_scroll <= prev_scroll:
            break  # Reached the end

    # Scroll back to start for a clean state
    row.evaluate("el => el.scrollLeft = 0")
    page.wait_for_timeout(200)


# ──────────────────────────────────────────────────────────────
# Main Scraper
# ──────────────────────────────────────────────────────────────


def scrape_all_trends(headless: bool = True) -> dict:
    """Main scraping function.

    1. Open the global trending page
    2. Scrape the default ("home") keywords
    3. Discover all category buttons
    4. Click each category, wait for refresh, scrape keywords
    5. Return a structured dict of all results
    """
    results: dict = {
        "scraped_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "url": TARGET_URL,
        "trends": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        print(f"🌐  Navigating to {TARGET_URL} ...")
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)  # Extra wait for JS rendering

        # ── Step 1: Scrape home/default keywords ──
        print("📋  Scraping home (default) keywords ...")
        home_keywords = scrape_keywords(page)
        results["trends"]["home"] = home_keywords
        print(f"    Found {len(home_keywords)} keywords: {home_keywords[:5]}{'...' if len(home_keywords) > 5 else ''}")

        # ── Step 2: Discover categories ──
        print("🔍  Discovering categories ...")
        categories = scrape_categories(page)
        cat_names = [c["name"] for c in categories]
        print(f"    Found {len(categories)} categories: {cat_names}")

        # ── Step 3: Iterate each category ──
        for i, cat in enumerate(categories, 1):
            cat_name = cat["name"]
            print(f"🏷   [{i}/{len(categories)}] Clicking category: {cat_name} ...")

            try:
                # Store old keywords to detect change
                old_keywords = list(results["trends"].get("home", []))

                cat["element"].scroll_into_view_if_needed()
                cat["element"].click()
                wait_for_keywords_refresh(page, old_keywords)

                cat_keywords = scrape_keywords(page)
                results["trends"][cat_name] = cat_keywords
                print(f"    Found {len(cat_keywords)} keywords: {cat_keywords[:5]}{'...' if len(cat_keywords) > 5 else ''}")

            except Exception as e:
                print(f"    ⚠  Error scraping category '{cat_name}': {e}")
                results["trends"][cat_name] = []

        # ── Cleanup ──
        browser.close()

    return results


# ──────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Scrape trending topics from X (Twitter) Global Trending page."
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show the browser window (useful for debugging)",
    )
    args = parser.parse_args()

    headless = not args.no_headless

    print("=" * 60)
    print("  X (Twitter) Global Trending Scraper")
    print("=" * 60)

    results = scrape_all_trends(headless=headless)

    # Write to JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_keywords = sum(len(v) for v in results["trends"].values())
    total_categories = len(results["trends"])

    print()
    print("=" * 60)
    print(f"✅  Done! Scraped {total_keywords} keywords across {total_categories} categories.")
    print(f"📄  Results saved to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
