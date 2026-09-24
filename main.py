import argparse
import csv
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, fields
from typing import Iterator, List, Optional, Set

from playwright.sync_api import Browser, Page, sync_playwright

LISTING_XPATH = '//a[contains(@href, "https://www.google.com/maps/place")]'
NAME_XPATH = '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]'
SEARCH_BOX_XPATH = "//form[contains(@jsaction,'searchboxFormSubmit')]//input[@name='q']"

@dataclass
class Place:
    name: str = ""
    address: str = ""
    website: str = ""
    phone_number: str = ""
    reviews_count: Optional[int] = None
    reviews_average: Optional[float] = None
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    store_delivery: str = "No"
    place_type: str = ""
    opens_at: str = ""
    introduction: str = ""
    url: str = ""

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

def extract_text(page: Page, xpath: str) -> str:
    try:
        if page.locator(xpath).count() > 0:
            return page.locator(xpath).inner_text()
    except Exception as e:
        logging.warning(f"Failed to extract text for xpath {xpath}: {e}")
    return ""

def extract_place(page: Page) -> Place:
    # XPaths
    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
    reviews_count_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'
    reviews_average_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'
    info1 = '//div[@class="LTs0Rc"][1]'
    info2 = '//div[@class="LTs0Rc"][2]'
    info3 = '//div[@class="LTs0Rc"][3]'
    opens_at_xpath = '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]'
    opens_at_xpath2 = '//div[@class="MkV9"]//span[@class="ZDu9vd"]//span[2]'
    place_type_xpath = '//div[@class="LBgpqf"]//button[@class="DkEaL "]'
    intro_xpath = '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]'

    place = Place()
    place.name = extract_text(page, NAME_XPATH)
    place.address = extract_text(page, address_xpath)
    place.website = extract_text(page, website_xpath)
    place.phone_number = extract_text(page, phone_number_xpath)
    place.place_type = extract_text(page, place_type_xpath)
    place.introduction = extract_text(page, intro_xpath) or "None Found"

    # Reviews Count
    reviews_count_raw = extract_text(page, reviews_count_xpath)
    if reviews_count_raw:
        try:
            temp = reviews_count_raw.replace('\xa0', '').replace('(','').replace(')','').replace(',','')
            place.reviews_count = int(temp)
        except Exception as e:
            logging.warning(f"Failed to parse reviews count: {e}")
    # Reviews Average
    reviews_avg_raw = extract_text(page, reviews_average_xpath)
    if reviews_avg_raw:
        try:
            temp = reviews_avg_raw.replace(' ','').replace(',','.')
            place.reviews_average = float(temp)
        except Exception as e:
            logging.warning(f"Failed to parse reviews average: {e}")
    # Store Info
    for idx, info_xpath in enumerate([info1, info2, info3]):
        info_raw = extract_text(page, info_xpath)
        if info_raw:
            temp = info_raw.split('·')
            if len(temp) > 1:
                check = temp[1].replace("\n", "").lower()
                if 'shop' in check:
                    place.store_shopping = "Yes"
                if 'pickup' in check:
                    place.in_store_pickup = "Yes"
                if 'delivery' in check:
                    place.store_delivery = "Yes"
    # Opens At
    opens_at_raw = extract_text(page, opens_at_xpath)
    if opens_at_raw:
        opens = opens_at_raw.split('⋅')
        if len(opens) > 1:
            place.opens_at = opens[1].replace(" ","")
        else:
            place.opens_at = opens_at_raw.replace(" ","")
    else:
        opens_at2_raw = extract_text(page, opens_at_xpath2)
        if opens_at2_raw:
            opens = opens_at2_raw.split('⋅')
            if len(opens) > 1:
                place.opens_at = opens[1].replace(" ","")
            else:
                place.opens_at = opens_at2_raw.replace(" ","")
    return place

def place_key(url: str) -> str:
    # Maps place URLs embed a stable feature id ("!1s0x...:0x..."); the rest varies by search.
    match = re.search(r"!1s(0x[0-9a-f]+:0x[0-9a-f]+)", url)
    return match.group(1) if match else url.split("?")[0]

def load_results(page: Page, query: str, total: int):
    # Force English: the parsing below (store options, hours) matches English text.
    page.goto("https://www.google.com/maps?hl=en", timeout=60000)
    page.locator(SEARCH_BOX_XPATH).fill(query)
    page.keyboard.press("Enter")
    page.wait_for_selector(LISTING_XPATH)
    page.locator(LISTING_XPATH).first.hover()
    previously_counted = 0
    stalls = 0
    while True:
        page.mouse.wheel(0, 10000)
        page.wait_for_timeout(1500)
        found = page.locator(LISTING_XPATH).count()
        logging.info(f"Currently Found: {found}")
        if found >= total:
            break
        if page.get_by_text("reached the end of the list").count() > 0:
            logging.info("Arrived at all available")
            break
        stalls = stalls + 1 if found == previously_counted else 0
        if stalls >= 3:
            logging.info("No new results after several scrolls, stopping")
            break
        previously_counted = found

def scrape_query(page: Page, query: str, total: int, seen: Set[str]) -> Iterator[Place]:
    logging.info(f"Searching: {query}")
    load_results(page, query, total)
    listings = page.locator(LISTING_XPATH).all()[:total]
    logging.info(f"Total Found: {len(listings)}")
    for idx, listing in enumerate(listings, 1):
        url = (listing.get_attribute("href") or "").split("?")[0]
        key = place_key(url)
        if key in seen:
            logging.info(f"Listing {idx} already scraped, skipping.")
            continue
        try:
            previous_name = extract_text(page, NAME_XPATH)
            listing.locator("xpath=..").click()
            try:
                # Wait for the detail pane to switch away from the previously opened place.
                page.wait_for_function(
                    """([xpath, previousName, key]) => {
                        const el = document.evaluate(xpath, document, null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        const name = el ? el.innerText.trim() : "";
                        return name && (name !== previousName || location.href.includes(key));
                    }""",
                    arg=[NAME_XPATH, previous_name, key],
                    timeout=10000,
                )
            except Exception:
                logging.warning(f"Detail pane for listing {idx} may not have refreshed.")
            time.sleep(1.5)  # Other fields render after the name
            place = extract_place(page)
            if place.name:
                place.url = url
                seen.add(key)
                yield place
            else:
                logging.warning(f"No name found for listing {idx}, skipping.")
        except Exception as e:
            logging.warning(f"Failed to extract listing {idx}: {e}")

def launch_browser(p) -> Browser:
    # Prefer an installed browser over Playwright's Chromium; Chrome first, Edge (ships with Windows) as backup.
    for channel in ("chrome", "msedge"):
        try:
            browser = p.chromium.launch(channel=channel, headless=False)
            logging.info(f"Using browser: {channel}")
            return browser
        except Exception:
            pass
    logging.info("Chrome and Edge not found, using Playwright's Chromium")
    return p.chromium.launch(headless=False)

def iter_places(queries: List[str], total: int) -> Iterator[Place]:
    seen: Set[str] = set()
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(locale="en-US")
        try:
            for query in queries:
                try:
                    yield from scrape_query(page, query, total, seen)
                except Exception as e:
                    logging.error(f"Search '{query}' failed: {e}")
        finally:
            browser.close()

def scrape_places(queries: List[str], total: int) -> List[Place]:
    """Scrape up to `total` places per query; returns whatever was collected even if interrupted."""
    setup_logging()
    places: List[Place] = []
    try:
        for place in iter_places(queries, total):
            places.append(place)
    except (KeyboardInterrupt, Exception) as e:
        logging.warning(f"Scrape stopped early ({type(e).__name__}: {e}); keeping {len(places)} places.")
    return places

def save_places_to_csv(places: List[Place], output_path: str = "result.csv", append: bool = False):
    if not places:
        logging.warning("No data to save.")
        return
    columns = [f.name for f in fields(Place)]
    write_header = not (append and os.path.isfile(output_path))
    with open(output_path, "a" if append else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if write_header:
            writer.writeheader()
        writer.writerows(asdict(place) for place in places)
    logging.info(f"Saved {len(places)} places to {output_path} (append={append})")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", action="append", help="Search query for Google Maps (repeat for several searches)")
    parser.add_argument("-t", "--total", type=int, default=1, help="Number of results to scrape per search")
    parser.add_argument("-o", "--output", type=str, default="result.csv", help="Output CSV file path")
    parser.add_argument("--append", action="store_true", help="Append results to the output file instead of overwriting")
    args = parser.parse_args()
    queries = args.search or ["turkish stores in toronto Canada"]
    places = scrape_places(queries, args.total)
    save_places_to_csv(places, args.output, append=args.append)

if __name__ == "__main__":
    main()
