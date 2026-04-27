import json
import os
import sys
import time
import pandas as pd
from playwright.sync_api import sync_playwright


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(BASE_DIR, "chrome_cookies.json")
EXCEL_FILE = os.path.join(BASE_DIR, "URL_TIMMINGS.xlsx")
PRIORITY_FILE = os.path.join(BASE_DIR, "priority.json")
CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.json")


def load_cookies():
    with open(COOKIE_FILE, "r") as f:
        return json.load(f)


def load_priority_order():
    if not os.path.exists(PRIORITY_FILE):
        return []
    with open(PRIORITY_FILE, "r") as f:
        data = json.load(f)
    return [(entry["subject"], entry["type"]) for entry in data]


def load_bot_config():
    defaults = {"headless": False, "slow_mo": 400}
    if not os.path.exists(CONFIG_FILE):
        return defaults
    with open(CONFIG_FILE, "r") as f:
        defaults.update(json.load(f))
    return defaults


def normalize(text: str):
    """Normalize text for comparison."""
    return text.replace("–", "-").replace("to", "-").replace("—", "-").lower().strip()


def enroll_in_block(page, course, ctype, target_string):
    print(f" Searching for timeslot block: {target_string}", flush=True)
    td_blocks = page.query_selector_all("td.not-available, td.available")
    for block in td_blocks:
        text = block.inner_text().strip()
        if normalize(target_string) in normalize(text):
            try:
                print(f" Clicking timeslot block: {text}", flush=True)
                link = block.query_selector("a")
                if link:
                    page.evaluate("(el) => el.click()", link)
                    print(f" Timeslot block clicked for {course} {ctype} → {target_string}", flush=True)
                    return True
            except Exception as e:
                print(f" Failed to click timeslot block: {e}", flush=True)
    print(f" No matching timeslot block found for {course} {ctype}", flush=True)
    return False


def main():
    priority_order = load_priority_order()
    config = load_bot_config()

    df = pd.read_excel(EXCEL_FILE, header=1, usecols=[1, 2, 3, 4])
    df.columns = ["SUBJECT", "TYPE", "STRING", "URL LINK"]
    df = df.dropna(subset=["SUBJECT", "TYPE", "STRING", "URL LINK"])
    for col in ["SUBJECT", "TYPE", "STRING", "URL LINK"]:
        df[col] = df[col].astype(str).str.strip()

    def get_priority(row):
        key = (row["SUBJECT"], row["TYPE"])
        return priority_order.index(key) if key in priority_order else 999

    df["PRIORITY"] = df.apply(get_priority, axis=1)
    df_sorted = df.sort_values(by="PRIORITY")

    print(f"\n🧠 Total enrolment steps: {len(df_sorted)}", flush=True)
    print(df_sorted[["SUBJECT", "TYPE", "URL LINK"]].to_string(), flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=bool(config.get("headless", False)),
            slow_mo=int(config.get("slow_mo", 400)),
        )
        context = browser.new_context()
        context.add_cookies(load_cookies())
        page = context.new_page()

        for _, row in df_sorted.iterrows():
            subject = row["SUBJECT"]
            ctype = row["TYPE"]
            target_string = row["STRING"]
            url = row["URL LINK"]

            if not url or url.lower().startswith("nan") or url.strip() == "":
                print(f"⚠️ Skipping {subject} {ctype}: Invalid URL", flush=True)
                continue

            print(f"\n Visiting {subject} {ctype} page...", flush=True)
            print(f"Opening: {url}", flush=True)

            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                if enroll_in_block(page, subject, ctype, target_string):
                    try:
                        print(" Waiting for 'ENROL NOW' button...", flush=True)
                        page.wait_for_selector("input[type='submit'][value='Enrol Now']", timeout=15000)
                        page.click("input[type='submit'][value='Enrol Now']")
                        print(" 'ENROL NOW' button clicked", flush=True)
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                    except Exception as e_btn:
                        print(f" Could not click 'ENROL NOW' button: {e_btn}", flush=True)
                else:
                    print(f" Skipping 'ENROL NOW' — timeslot block not found for {subject} {ctype}", flush=True)
            except Exception as e:
                print(f" Error on {subject} {ctype}: {e}", flush=True)

        print("\n All enrolment steps processed. Browser will close in 5 seconds...", flush=True)
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
