import time
import httpx
from bs4 import BeautifulSoup

from scraper.models import Car
from scraper.phone_scraper import get_phone_number_from_car_page
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


def parse_car_details(url: str, client: httpx.Client) -> dict:
    response = client.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        title = soup.select_one("h1.head").get_text(strip=True)
        price_usd = int(soup.select_one(".price_value strong").get_text(strip=True)
                        .replace(" ", "")
                        .replace("$", "")
                        .replace("€", "")
                        .replace("грн", ""))
        odometer = int(soup.select_one("span.size18").get_text(strip=True) + "000")
        username = soup.select_one(".seller_info_name").get_text(strip=True)
        phone_number = format_phone_number(get_phone_number_from_car_page(url))

        image_tag = soup.select_one("div.photo-620x465 img")
        image_url = image_tag.get("src") if image_tag else ""

        images_count = len(soup.select(".photo-74x56.loaded")) + 1

        car_number = None
        car_number_tag = soup.select_one("span.state-num.ua")
        if car_number_tag:
            car_number = car_number_tag.get_text(strip=True).split("Ми розпізнали")[0].strip()

        vin_tag = soup.select_one("span.label-vin")
        car_vin = vin_tag.get_text(strip=True) if vin_tag else None

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

    except Exception as a:
        print(a)
        return {}


def main(start_page: int=1, stop_page: int=2) -> None:
    all_cars = []

    with httpx.Client() as client:
        for page in range(start_page, stop_page):
            print(f"Parsing page {page}")
            car_urls = get_car_urls_from_page(page, client)
            print(f"Found {len(car_urls)} cars")

            for url in car_urls:
                data = parse_car_details(url, client)
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
