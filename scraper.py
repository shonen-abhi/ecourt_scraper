import os
import time
import base64
from typing import List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://newdelhi.dcourts.gov.in/cause-list-%e2%81%84-daily-board/"

def _make_driver(headless: bool = False):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return driver

def get_court_complexes() -> List[Tuple[str, str]]:
    driver = _make_driver(headless=True)
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 20)
        sel = wait.until(EC.presence_of_element_located((By.ID, "est_code")))
        select = Select(sel)
        complexes = []
        for opt in select.options:
            text = opt.text.strip()
            val = opt.get_attribute("value").strip()
            if text and val:
                complexes.append((text, val))
        return complexes
    finally:
        driver.quit()

def get_judges_for_complex(complex_value: str) -> List[Tuple[str, str]]:
    driver = _make_driver(headless=True)
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 20)
        sel = wait.until(EC.presence_of_element_located((By.ID, "est_code")))
        Select(sel).select_by_value(complex_value)
        time.sleep(1.2)
        court_sel = wait.until(EC.presence_of_element_located((By.ID, "court")))
        select = Select(court_sel)
        judges = []
        for opt in select.options:
            text = opt.text.strip()
            val = opt.get_attribute("value").strip()
            if text and val:
                judges.append((text, val))
        return judges
    finally:
        driver.quit()

def open_and_fill_then_download(date_str: str, complex_value: str, judge_value: str, download_dir: str = "downloads"):
    """
    Opens the site in a visible Chrome window, auto-fills date, complex, and judge.
    Then waits for the user to manually solve CAPTCHA and click Search.
    After that, automatically saves the page as PDF using Chrome CDP.
    """
    os.makedirs(download_dir, exist_ok=True)
    driver = _make_driver(headless=False)
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 30)

        # --- Fill date ---
        date_input = wait.until(EC.presence_of_element_located((By.ID, "date")))
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))",
            date_input,
            date_str
        )
        print("[+] Date set to", date_str)

        # --- Select court complex ---
        est_sel = wait.until(EC.presence_of_element_located((By.ID, "est_code")))
        Select(est_sel).select_by_value(complex_value)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", est_sel)
        time.sleep(1)
        print("[+] Court complex selected:", complex_value)

        # --- Select judge ---
        court_sel = wait.until(EC.presence_of_element_located((By.ID, "court")))
        Select(court_sel).select_by_value(judge_value)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", court_sel)
        print("[+] Judge selected:", judge_value)

        print("\n==============================")
        print("Form has been auto-filled!")
        print("Now please solve the CAPTCHA and click 'Search' manually in Chrome.")
        input("Press Enter *after* you have searched and results are visible...")

        # --- Save page as PDF using Chrome DevTools Protocol ---
        pdf_path = os.path.join(download_dir, f"cause_list_{date_str.replace('/', '-')}.pdf")
        print("[+] Saving PDF to:", pdf_path)

        result = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "landscape": False,
                "paperWidth": 8.27,   # A4 size in inches
                "paperHeight": 11.69,
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4
            }
        )
        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(result['data']))
        print(f"PDF saved successfully: {pdf_path}")

    finally:
        print("\nPress Enter to close the browser...")
        input()
        driver.quit()
