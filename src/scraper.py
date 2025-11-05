import os

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PWTimeoutError

from src.config import Config
from src.dirs import HTML_OUTPUT_DIR

# --- Selectors / constants ---
BASE_LEADERBOARD_URL_TEMPLATE = (
    "https://www.linkedin.com/games/{game}/results/leaderboard/connections/"
)
TARGET_BUTTON_ID = "#connections-leaderboard-see-more-button"
CONTENT_SELECTOR = ".pr-connections-leaderboard__content"
POSSIBLE_LOADER = ".artdeco-loader"  # common LinkedIn loader
LOGIN_HINT_SELECTORS = [
    'input[name="session_key"]',
    'input[name="username"]',
    'form[action*="login"]',
]


def _detect_need_login(page) -> bool:
    for sel in LOGIN_HINT_SELECTORS:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False


def process_one_url(page: Page, url: str) -> str:
    """Opens the site, potentially waits for login and reads the table.

    Returns:
        html string of the leaderboard element
    """
    page.set_default_timeout(20_000)
    print(f"\n➡️  Visiting: {url}")
    page.goto(url, wait_until="domcontentloaded")

    # Detect login and wait until content appears after manual login
    try:
        page.wait_for_selector(CONTENT_SELECTOR, timeout=5000)
    except PWTimeoutError:
        if _detect_need_login(page):
            print("⚠️ Please log in manually in the opened window…")
            page.wait_for_selector(CONTENT_SELECTOR, timeout=300_000)
            print("✅ Logged in, continuing.")

    content = page.locator(CONTENT_SELECTOR).first
    content.wait_for(state="visible", timeout=20_000)

    # Before HTML length (to detect change)
    before_len = len(content.inner_html())

    # --- START: CLICK AND WAIT LOGIC ---
    try:
        button = page.locator(TARGET_BUTTON_ID)
        if button.count() > 0:
            print("🔘 Clicking 'See more' button...")
            button.click()

            # Strategy 1: Wait for the loader to appear and disappear (Most reliable)
            print("... Waiting for content to load (loader strategy)...")
            try:
                loader = page.locator(POSSIBLE_LOADER)
                # Wait for it to appear (short timeout)
                loader.wait_for(state="visible", timeout=5000)
                print("... Loader detected, waiting for it to finish...")
                # Wait for it to disappear (long timeout)
                loader.wait_for(state="hidden", timeout=20_000)
                print("✅ Content loaded (loader disappeared).")

            except PWTimeoutError:
                print("... Loader strategy failed. Trying content-length check...")

                # Strategy 2: Wait for content length to change
                _ = page.wait_for_function(
                    """(args) => {
                        const [selector, old_len] = args;
                        const el = document.querySelector(selector);
                        // Check if element exists AND its HTML is longer
                        return el && el.innerHTML.length > old_len;
                    }""",
                    arg=[CONTENT_SELECTOR, before_len],
                    timeout=15000,
                )
                print("✅ Content loaded (HTML length changed).")

        else:
            print("ℹ️ 'See more' button not found; proceeding.")

    except PWTimeoutError:
        print("⏱️ Timed out waiting for content to change; saving current HTML.")
    except Exception as e:
        print(f"⚠️ Error during click/wait (continuing): {e}")
    # --- END: CLICK AND WAIT LOGIC ---

    # Save the content HTML
    # By this point, the wait has either succeeded or timed out.
    # We now get the *current* inner_html, which will be the new,
    # updated HTML if the wait was successful.
    content.wait_for(state="visible", timeout=20_000)
    return content.inner_html()


def download_leaderboards_for_urls(
    named_urls: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Goest through all urls, downloads and returns html of leaderboard elements"""
    with sync_playwright() as p:
        # Single persistent context so you log in once for all URLs
        context = p.firefox.launch_persistent_context(
            user_data_dir="./playwright_profile",
            headless=False,
        )
        try:
            # Use a single page (or open/close per URL if you prefer isolation)
            page = context.new_page()
            results: list[tuple[str, str]] = []
            for name, url in named_urls:
                try:
                    leaderboard_html = process_one_url(page, url)
                    results.append((name, leaderboard_html))
                except Exception as e:
                    print(f"❌ Error on {url}: {e}")
            return results
        finally:
            context.close()


def save_scraped_html_to_cache(scraped_html: list[tuple[str, str]]):
    if not os.path.isdir(HTML_OUTPUT_DIR):
        os.makedirs(HTML_OUTPUT_DIR)

    for game_name, html in scraped_html:
        output_path = os.path.join(HTML_OUTPUT_DIR, game_name + ".html")

        with open(output_path, "w", encoding="utf8") as f:
            _ = f.write(html)


def scraper_main(config: Config):
    named_urls = [
        (game, BASE_LEADERBOARD_URL_TEMPLATE.format(game=game))
        for game in config["games"]
    ]

    scraped_html = download_leaderboards_for_urls(named_urls)

    save_scraped_html_to_cache(scraped_html)

    print(
        f"Succesfully saved {len(scraped_html)} game leaderboards into cache ({HTML_OUTPUT_DIR}). Proceed with the parse command!"
    )
