from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from pathlib import Path
from urllib.parse import urlparse
import re

# --- Selectors / constants ---
TARGET_BUTTON_ID = "#connections-leaderboard-see-more-button"
CONTENT_SELECTOR = ".pr-connections-leaderboard__content"
POSSIBLE_LOADER = ".artdeco-loader"  # common LinkedIn loader
LOGIN_HINT_SELECTORS = [
    'input[name="session_key"]',
    'input[name="username"]',
    'form[action*="login"]',
]


# --- Helpers ---
def _slug_from_url(url: str) -> str:
    """Create a readable, filesystem-safe slug for file naming."""
    p = urlparse(url)
    slug = f"{p.netloc}{p.path}".strip("/").replace("/", "_")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", slug)
    return slug or "page"


def _wait_for_content_change(page, before_len: int, timeout_ms: int = 15000):
    """Wait for loader to vanish or for innerHTML length to change."""
    try:
        if page.locator(POSSIBLE_LOADER).first.is_visible():
            page.locator(POSSIBLE_LOADER).first.wait_for(
                state="hidden", timeout=timeout_ms
            )
            return
    except Exception:
        pass

    page.wait_for_function(
        """([sel, lenBefore]) => {
            const el = document.querySelector(sel);
            if (!el) return false;
            return el.innerHTML.length !== lenBefore;
        }""",
        arg=[CONTENT_SELECTOR, before_len],
        timeout=timeout_ms,
    )


def _detect_need_login(page) -> bool:
    for sel in LOGIN_HINT_SELECTORS:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False


def process_one_url(page: Page, url: str, out_dir: Path) -> Path:
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

    # --- START: REVISED CLICK AND WAIT LOGIC ---
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
                # This catches timeout from EITHER wait_for (visible or hidden)
                print("... Loader strategy failed. Trying content-length check...")

                # Strategy 2: Wait for content length to change (Your original goal)
                page.wait_for_function(
                    """(args) => {
                        const [selector, old_len] = args;
                        const el = document.querySelector(selector);
                        // Check if element exists AND its HTML is longer
                        return el && el.innerHTML.length > old_len;
                    }""",
                    [CONTENT_SELECTOR, before_len],  # Pass args as a list
                    timeout=15000,
                )
                print("✅ Content loaded (HTML length changed).")

        else:
            print("ℹ️ 'See more' button not found; proceeding.")

    except PWTimeoutError:
        # This will be caught if Strategy 2 (wait_for_function) times out
        print("⏱️ Timed out waiting for content to change; saving current HTML.")
    except Exception as e:
        print(f"⚠️ Error during click/wait (continuing): {e}")
    # --- END: REVISED CLICK AND WAIT LOGIC ---

    # Save the content HTML
    # By this point, the wait has either succeeded or timed out.
    # We now get the *current* inner_html, which will be the new,
    # updated HTML if the wait was successful.
    content.wait_for(state="visible", timeout=20_000)
    html = content.inner_html()

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_slug_from_url(url)}.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"✅ Saved HTML to: {out_path}")
    return out_path


def download_leaderboards_for_urls(
    urls: list[str], output_dir: str = "leaderboards_out"
):
    out_dir = Path(output_dir)

    with sync_playwright() as p:
        # Single persistent context so you log in once for all URLs
        context = p.firefox.launch_persistent_context(
            user_data_dir="./playwright_profile",
            headless=False,
        )
        try:
            # Use a single page (or open/close per URL if you prefer isolation)
            page = context.new_page()
            results = []
            for url in urls:
                try:
                    path = process_one_url(page, url, out_dir)
                    results.append((url, str(path)))
                except Exception as e:
                    print(f"❌ Error on {url}: {e}")
            return results
        finally:
            context.close()


def scraper_main():
    URLS = [
        "https://www.linkedin.com/games/zip/results/leaderboard/connections/",
        "https://www.linkedin.com/games/queens/results/leaderboard/connections/",
        "https://www.linkedin.com/games/tango/results/leaderboard/connections/",
        "https://www.linkedin.com/games/mini-sudoku/results/leaderboard/connections/",
    ]
    download_leaderboards_for_urls(URLS, output_dir="leaderboards_out")


if __name__ == "__main__":
    URLS = [
        "https://www.linkedin.com/games/zip/results/leaderboard/connections/",
        "https://www.linkedin.com/games/queens/results/leaderboard/connections/",
        "https://www.linkedin.com/games/tango/results/leaderboard/connections/",
        "https://www.linkedin.com/games/mini-sudoku/results/leaderboard/connections/",
    ]
    download_leaderboards_for_urls(URLS, output_dir="leaderboards_out")
