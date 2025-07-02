import time
import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scraper.models import Car
from utils.helpers import format_phone_number


START_URL = "https://auto.ria.com/uk/car/used/"


def get_car_urls_from_page(page: int, client: httpx.Client) -> list:
    response = client.get(START_URL, params={"page": page})
    soup = BeautifulSoup(response.content, "html.parser")

    links = []

    for car in soup.find_all("a", class_="m-link-ticket"):
        url = car.get("href")
        if url:
            links.append(url)

    return links


def parse_car_details_with_browser(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        try:
            page.goto(url, timeout=30000)

            page.evaluate("""
                const banner = document.querySelector('.c-notifier-container');
                if (banner) banner.remove();
            """)

            try:
                page.click(".phone_show_link", timeout=20000)
            except:
                pass

            page.wait_for_selector(".popup-successful-call-desk", timeout=25000)

            title = page.query_selector("h1.head").inner_text().strip()
            price_usd = None

            main_price_block = page.query_selector(".price_value strong")
            if main_price_block:
                text = main_price_block.inner_text().strip()
                price_usd = text if "$" in text else None

            if price_usd is None:
                alt_price_blocks = page.query_selector_all('[data-currency="USD"]')
                for block in alt_price_blocks:
                    text = block.inner_text().strip()
                    price_usd = text if text else None

            if price_usd is None:
                price_usd = 0
            else:
                price_usd = int("".join([let for let in price_usd if let.isdigit()]))

            odometer_raw = page.query_selector("span.size18").inner_text().strip()
            odometer = int(odometer_raw + "000") if odometer_raw.isdigit() else 0
            username = page.query_selector(".seller_info_name").inner_text().strip()

            phone_element = page.query_selector(".popup-successful-call-desk")
            phone_number = format_phone_number(phone_element.inner_text().strip()) if phone_element else "error"

            image_tag = page.query_selector("div.photo-620x465 img")
            image_url = image_tag.get_attribute("src") if image_tag else ""

            images_count = len(page.query_selector_all(".photo-74x56.loaded"))

            car_number = None
            car_number_tag = page.query_selector("span.state-num.ua")
            if car_number_tag:
                car_number_text = car_number_tag.inner_text().strip()
                car_number = car_number_text.split("Ми розпізнали")[0].strip()

            vin_tag = page.query_selector("span.label-vin")
            car_vin = vin_tag.inner_text().strip() if vin_tag else None

            return {
                "url": url,
                "title": title,
                "price_usd": price_usd,
                "odometer": odometer,
                "username": username,
                "phone_number": phone_number,
                "image_url": image_url,
                "images_count": images_count,
                "car_number": car_number,
                "car_vin": car_vin,
            }

        except Exception as e:
            print(f"{url} worked with error:")
            print(e)
            return {}

        finally:
            browser.close()


def main(start_page: int=1, stop_page: int=2) -> None:
    all_cars = []

    with httpx.Client() as client:
        for page in range(start_page, stop_page):
            print(f"Parsing page {page}")
            car_urls = get_car_urls_from_page(page, client)
            print(f"Found {len(car_urls)} cars")

            for url in car_urls:
                data = parse_car_details_with_browser(url)
                if data:
                    all_cars.append(data)

    for car in all_cars:
        obj, created = Car.objects.update_or_create(
            url=car["url"],
            defaults={
                "title": car["title"],
                "price_usd": car["price_usd"],
                "odometer": car["odometer"],
                "username": car["username"],
                "phone_number": car["phone_number"],
                "image_url": car["image_url"],
                "images_count": car["images_count"],
                "car_number": car["car_number"],
                "car_vin": car["car_vin"],
            }
        )
        print(f"{obj} was {"created" if created else "updated"}")


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    duration = time.perf_counter() - start
    print(f"Completed in {duration} seconds")
