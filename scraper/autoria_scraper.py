import os
import django
import asyncio
import time

from asgiref.sync import sync_to_async
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scraper_core.settings")
django.setup()

from scraper.models import Car
from utils.helpers import format_phone_number

START_URL = "https://auto.ria.com/uk/car/used/"


async def get_car_urls_from_page(page: int, client: httpx.AsyncClient) -> list[str]:
    resp = await client.get(START_URL, params={"page": page})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    return [
        a["href"]
        for a in soup.find_all("a", class_="m-link-ticket", href=True)
    ]


async def parse_car_details_with_browser(
    url: str,
    browser,
    semaphore: asyncio.Semaphore
) -> dict:
    async with (semaphore):
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        try:
            await page.goto(url, timeout=30_000)

            await page.evaluate("""
                const b = document.querySelector('.c-notifier-container');
                if (b) b.remove();
            """)

            await page.click(".phone_show_link", timeout=20_000)
            await page.locator(".popup-successful-call-desk").first.wait_for(state="visible", timeout=25_000)

            title = ""
            title_locator = page.locator("h1.head").first
            if await title_locator.count():
                title = (await title_locator.inner_text()).strip()

            price_text = None
            main_block = page.locator(".price_value strong")
            if await main_block.count():
                txt = (await main_block.first.inner_text()).strip()
                if "$" in txt:
                    price_text = txt

            if not price_text:
                usd_blocks = await page.locator('[data-currency="USD"]').all()
                for block in usd_blocks:
                    txt = (await block.inner_text()).strip()
                    if txt:
                        price_text = txt
                        break

            price_usd = int("".join([el for el in price_text if el.isdigit()])) if price_text else 0

            odometer = 0
            odo_locator = page.locator("section.main-info span.size18").first
            odometer_raw = ""
            if await odo_locator.count():
                odometer_raw = (await odo_locator.inner_text()).strip()
            if odometer_raw.isdigit():
                odometer = int(odometer_raw + "000")

            username = ""
            user_locator = page.locator(".seller_info_name").first
            if await user_locator.count():
                username = (await user_locator.inner_text()).strip()

            el = page.locator(".popup-successful-call-desk")
            text = await el.first.text_content()
            phone_number = format_phone_number(text.strip())

            image_url = ""
            img = page.locator("div.photo-620x465 img")
            if await img.count():
                image_url = await img.first.get_attribute("src")

            images_count = await page.locator(".photo-74x56.loaded").count()

            car_number = None
            num_tag = page.locator("span.state-num.ua")
            if await num_tag.count():
                raw = (await num_tag.first.inner_text()).strip()
                car_number = raw.split("Ми розпізнали")[0].strip()

            vin = None
            vin_tag = page.locator("span.label-vin")
            if await vin_tag.count():
                vin = (await vin_tag.first.inner_text()).strip()


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
                "car_vin": vin,
            }

        except Exception as e:
            return {}
        finally:
            await page.close()


@sync_to_async
def save_car_to_db(data: dict):
    try:
        obj, created = Car.objects.update_or_create(
            url=data["url"],
            defaults={
                "title": data["title"],
                "price_usd": data["price_usd"],
                "odometer": data["odometer"],
                "username": data["username"],
                "phone_number": data["phone_number"],
                "image_url": data["image_url"],
                "images_count": data["images_count"],
                "car_number": data["car_number"],
                "car_vin": data["car_vin"],
            }
        )
    except Exception as e:
        print(data["url"])
        print(e)
    return obj, created


async def main(start_page: int = 1, stop_page: int = 3):
    sem = asyncio.Semaphore(3)
    async with httpx.AsyncClient() as client, async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        url_tasks = [
            get_car_urls_from_page(pg, client)
            for pg in range(start_page, stop_page)
        ]
        pages_lists = await asyncio.gather(*url_tasks)
        all_urls = [u for sub in pages_lists for u in sub]
        print(f"Total URLs to parse: {len(all_urls)}")

        parse_tasks = [
            parse_car_details_with_browser(u, browser, sem)
            for u in all_urls
        ]
        cars_data = await asyncio.gather(*parse_tasks)

        save_tasks = [
            save_car_to_db(d) for d in cars_data if d
        ]
        results = await asyncio.gather(*save_tasks)

        created_cars = 0
        updated_cars = 0

        for obj, created in results:
            if created:
                created_cars += 1
            else:
                updated_cars += 1

        print(f"{created_cars} was created")
        print(f"{updated_cars} was updated")

        await browser.close()


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main(start_page=1, stop_page=2))
    duration = time.perf_counter() - start
    print(f"Completed in {duration} seconds")
