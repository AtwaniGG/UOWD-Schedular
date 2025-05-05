Timetable Automation Bot
========================

This Python script automates enrolling in your university’s SOLS tutorial, lab and lecture timeslots. It reads your desired subjects, timeslot identifiers and direct enrollment URLs from an Excel file, then drives a real browser session (via Playwright) to select and confirm each slot in priority order.

Contents
--------
• timetable_bot.py  
• convert_cookies.py  
• URL_TIMMINGS.xlsx    
• README.txt ← this file  

Prerequisites
-------------
• Python 3.x  
• Google Chrome (or Chromium) installed  

Dependencies
------------
Install the following Python packages before running:
• pandas  
• playwright  
• openpyxl  

Cookie Export & Conversion
--------------------------
1. Install the “Get cookies.txt” Chrome extension (or similar).  
2. Log in to SOLS in Chrome, then use the extension to export your session cookies as cookies.txt.  
3. Convert that file into the JSON format Playwright needs by running:  
   python3 convert_cookies.py  
   This reads cookies.txt and writes chrome_cookies.json in this folder.  

Setup
-----
1. Install dependencies:  
   pip install pandas playwright openpyxl  
   playwright install  
2. Edit URL_TIMMINGS.xlsx:  
   – Header row (row 2) must read exactly: SUBJECT | TYPE | STRING | URL LINK  
   – Add one row per enrollment target:  
     • SUBJECT: course code (e.g. CSCI203)  
     • TYPE: COMPUTER LAB, TUTORIAL or LECTURE  
     • STRING: exact timeslot block text from SOLS (copy-paste)  
     • URL LINK: direct SOLS URL for that timeslot page  
3. (Optional) Adjust PRIORITY_ORDER in timetable_bot.py to change the sequence.  

Usage
-----
From this folder, run:  
python3 timetable_bot.py  

The script will:  
1. Open Chrome (visible) and load your converted cookies.  
2. Read and sort your enrollment steps.  
3. Visit each URL, click the matching timeslot block, then click ENROL NOW.  
4. Wait for the redirect back to tutorial home, then repeat.  
5. Pause at the end for manual confirmation.  

Troubleshooting
---------------
• “about:blank” on startup?  
  – Check that URL LINK cells are non-empty and valid.  
  – Ensure URL_TIMMINGS.xlsx and chrome_cookies.json are in this folder.  

• Playwright errors  
  – Confirm you ran pip install pandas playwright openpyxl and playwright install.  

• Timeslot blocks not found?  
  – Verify the STRING column matches exactly what SOLS shows.  
  – Adjust the normalize() function in the script if SOLS uses special characters.  

• “ENROL NOW” button not detected?  
  – Inspect the confirmation page and update the selector if the button text or tag differs.  

Safety & Ethics
---------------
Use this bot responsibly. Automate only your own account and respect the university’s policies. You remain responsible for your final timetable.

Enjoy your automated tutorial enrolment!

