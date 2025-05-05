import json
import pandas as pd
import time
from playwright.sync_api import sync_playwright


COOKIE_FILE = "chrome_cookies.json" # name of Json File
EXCEL_FILE = "URL_TIMMINGS.xlsx" #Name of Excel File

#Make a list with your desired class name and type. The list below is an example it could be changed to your desires.
PRIORITY_ORDER = [
    ("CSCI203", "COMPUTER LAB"),
    ("CSIT127", "COMPUTER LAB"),
    ("CSCI251", "COMPUTER LAB"),
    ("CSIT314", "COMPUTER LAB"),
    ("CSIT314", "TUTORIAL"),
    ("CSIT127", "TUTORIAL"),
    ("CSCI251", "LECTURE"),
    ("CSIT314", "LECTURE"),
    ("CSCI203", "LECTURE"),
    ("CSIT127", "LECTURE"),
]

def load_cookies():
    with open(COOKIE_FILE, "r") as f:
        return json.load(f)

def normalize(text: str):
    """Normalize text for comparison."""
    return text.replace("–", "-").replace("to", "-").replace("—", "-").lower().strip()

def enroll_in_block(page, course, ctype, target_string):
    """
    Looks for a timeslot block by checking all <td> elements having class 
    "not-available" or "available" and clicks the link inside the one 
    whose text matches target_string.
    """
    print(f" Searching for timeslot block: {target_string}")
    td_blocks = page.query_selector_all("td.not-available, td.available")
    for block in td_blocks:
        text = block.inner_text().strip()
        if normalize(target_string) in normalize(text):
            try:
                print(f"👉 Clicking timeslot block: {text}")
                link = block.query_selector("a")
                if link:
                    page.evaluate("(el) => el.click()", link)
                    print(f" Timeslot block clicked for {course} {ctype} → {target_string}")
                    return True
            except Exception as e:
                print(f" Failed to click timeslot block: {e}")
    print(f" No matching timeslot block found for {course} {ctype}")
    return False

def main():
    # ---- STEP 1: Load and clean the Excel data ----
    # The data is in columns 1-4 from the sheet (header=1) so we use usecols=[1,2,3,4]
    df = pd.read_excel(EXCEL_FILE, header=1, usecols=[1, 2, 3, 4])
    df.columns = ["SUBJECT", "TYPE", "STRING", "URL LINK"]
    df = df.dropna(subset=["SUBJECT", "TYPE", "STRING", "URL LINK"])
    for col in ["SUBJECT", "TYPE", "STRING", "URL LINK"]:
        df[col] = df[col].astype(str).str.strip()

    # ---- STEP 2: Apply custom priority order ----
    def get_priority(row):
        key = (row["SUBJECT"], row["TYPE"])
        return PRIORITY_ORDER.index(key) if key in PRIORITY_ORDER else 999
    df["PRIORITY"] = df.apply(get_priority, axis=1)
    df_sorted = df.sort_values(by="PRIORITY")
    
    print(f"\n🧠 Total enrolment steps: {len(df_sorted)}")
    print(df_sorted[["SUBJECT", "TYPE", "URL LINK"]])
    
    # ---- STEP 3: Process each enrolment step using Playwright ----
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        context = browser.new_context()
        context.add_cookies(load_cookies())
        page = context.new_page()

        for _, row in df_sorted.iterrows():
            subject = row["SUBJECT"]
            ctype = row["TYPE"]
            target_string = row["STRING"]
            url = row["URL LINK"]

            if not url or url.lower().startswith("nan") or url.strip() == "":
                print(f"⚠️ Skipping {subject} {ctype}: Invalid URL")
                continue

            print(f"\n Visiting {subject} {ctype} page...")
            print(f"Opening: {url}")

            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                time.sleep(1)
                
                # Step 1: Click the timeslot block
                if enroll_in_block(page, subject, ctype, target_string):
                    # Step 2: Wait for and click the "ENROL NOW" button
                    try:
                        print("➡️ Waiting for 'ENROL NOW' button...")
                        # Wait up to 15 seconds for the button
                        page.wait_for_selector("input[type='submit'][value='Enrol Now']", timeout=15000)
                        page.click("input[type='submit'][value='Enrol Now']")
                        print("ENROL NOW' button clicked")
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                    except Exception as e_btn:
                        print(f" Could not click 'ENROL NOW' button: {e_btn}")
                else:
                    print(f" Skipping 'ENROL NOW' — timeslot block not found for {subject} {ctype}")
            except Exception as e:
                print(f" Error on {subject} {ctype}: {e}")

        print("\n All enrolment steps processed. Check your timetable or the site to confirm.")
        input(" Press Enter to close the browser...")
        browser.close()

if __name__ == "__main__":
    main()
