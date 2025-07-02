from playwright.sync_api import sync_playwright


def get_phone_number_from_car_page(url: str) -> str:
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
            phone = page.query_selector(".popup-successful-call-desk")
            return phone.inner_text().strip() if phone else "error"

        except Exception as e:
            print(e)
            return "error"
        finally:
            browser.close()
