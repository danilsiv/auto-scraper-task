import os
import sys
import time
import asyncio
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scraper_core.settings")
django.setup()

from datetime import datetime, timedelta
from dotenv import load_dotenv

from scraper.autoria_scraper import main

load_dotenv()

SCRAPER_HOUR = int(os.getenv("SCRAPER_RUN_HOUR", datetime.now().hour))
SCRAPER_MINUTE = int(os.getenv("SCRAPER_RUN_MINUTE", datetime.now().minute + 1))
START_PAGE = int(os.getenv("START_PAGE", 1))
STOP_PAGE = int(os.getenv("STOP_PAGE", 21))


def seconds_until_next_run(hour: int, minute: int) -> int:
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return int((next_run - now).total_seconds())


def run_scraper():
    asyncio.run(main(START_PAGE, STOP_PAGE))


def main_loop():
    while True:
        sleep_seconds = seconds_until_next_run(SCRAPER_HOUR, SCRAPER_MINUTE)
        hours = sleep_seconds // 3600
        minutes = sleep_seconds % 3600 // 60
        print(f"Sleeping for {hours} hours {minutes} minutes")
        time.sleep(sleep_seconds)

        print(f"Running scraper...")
        start = time.perf_counter()
        run_scraper()
        duration = time.perf_counter() - start
        print(f"Completed in {duration} seconds")

        time.sleep(60)


if __name__ == "__main__":
    main_loop()
