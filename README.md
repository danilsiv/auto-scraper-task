# Auto.ria Scraper

## Project Description
A web-based Django application for scheduled scraping of car listings from [auto.ria.com](https://auto.ria.com/car/used/), storing the data in a PostgreSQL database, and exporting it to JSON format immediately after scraping.

## Features
- Scheduled scraping of car listings from auto.ria.com.
- Data is saved in a PostgreSQL database.
- Automatic database export (JSON dump) after each scraping session.
- Django admin panel for browsing stored data.
- Dockerized setup with three services: database, Django app, and scraper service running automatically.

## Technologies Used
- **Backend:** Django Framework
- **Scraping:** Playwright
- **Database:** PostgreSQL
- **Task Control:** Custom scheduled script (can be extended with Celery)

---

## Installation
### Python 3 must be installed

1. **Clone the repository and open with PyCharm:**
   ```bash
   git clone https://github.com/danilsiv/auto-scraper-task.git
   
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Linux/Mac
   venv\Scripts\activate     # For Windows
   
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   
4. **Install Playwright browsers (required for scraping):**
   ```bash
   playwright install

5. **Create a .env file:**
   ```bash
   cp .env.sample .env
   ```
   By default, the .env contains important scraping parameters commented out:
   ```bash
   # START_PAGE=1
   # STOP_PAGE=20
   
   # SCRAPER_RUN_HOUR=12
   # SCRAPER_RUN_MINUTE=30
   ```
   If you run the scraper without setting these explicitly, it will:
   - Start scraping automatically within about one minute of launch.
   - Scrape pages 1 through 20 by default (~400 detailed car pages, ~420 total requests).
   - After scraping, immediately dump the database to JSON (db_dumps/dump_YYYYMMDD.json).


6. **Start PostgreSQL via Docker (if using local DB):**
   ```bash
   docker-compose up -d db

7. **Apply database migrations:**
   ```bash
   python manage.py migrate
   
8. **Start the scraping process manually (optional):**
   ```bash
   python scraper/run_daily_scraper.py


## Docker Compose Setup

The project runs with three Docker services:
- db — PostgreSQL database.
- web — Django application serving the API and admin panel.
- scraper — scraper service which:
   - Waits for the scheduled time (or starts scraping within a minute by default).
   - Scrapes auto.ria pages (default: 20 pages).
   - Saves data to the database.
   - Dumps data to JSON after scraping.

1. **Configure environment:**
   ```bash
   cp .env.sample .env

2. **Change the value of `POSTGRES_HOST` in `.env` from `localhost` to `db`, which is the service name used in Docker Compose.**


3. **Build and run containers:**
   ```bash
   docker-compose up --build

#### This command will:

- Start a PostgreSQL database.
- Launch the Django server (on port 8001).
- Run the scraping script in a separate container (scraper) which:
  - Waits for the time specified in .env
  - Scrapes listings from Auto.ria
  - Stores them in the database
  - Immediately exports the data to a JSON file (saved to db_dumps/)

### Important Notes
- The scraper ignores pages with a new site structure that cause failures. As a result, around 5–10% of cars may be missed.
- Occasionally, the scraper encounters timeouts due to network instability or site delays, causing minor data loss (a very small percentage of cars).
- Setting explicit values in .env for start/stop pages and scraping time ensures predictable behavior.
- JSON dumps are stored under db_dumps/ with filenames like dump_YYYYMMDD.json.

### Django Admin Panel

Access at:
`http://localhost:8001/admin/`

Create a superuser with:
```bash
python manage.py createsuperuser
```
