import requests
from bs4 import BeautifulSoup
import getpass
import urllib3
import time
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGIN_URL = "https://app.ktu.edu.in/login.htm"
RESULT_PAGE_URL = "https://app.ktu.edu.in/eu/res/semesterGradeCardListing.htm"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}


def request_with_retry(method, url, max_retries=50, base_delay=3, max_delay=15, **kwargs):
    """
    Retry a request until it succeeds (status 200) or we exhaust retries.
    Uses jittered backoff so we don't hammer the server in lockstep with
    everyone else also retrying.
    """
    kwargs.setdefault("timeout", 15)
    for attempt in range(1, max_retries + 1):
        try:
            resp = method(url, **kwargs)
            if resp.status_code == 200:
                return resp
            print(f"[Attempt {attempt}] Got HTTP {resp.status_code}, retrying...")
        except requests.exceptions.Timeout:
            print(f"[Attempt {attempt}] Request timed out, retrying...")
        except requests.exceptions.RequestException as e:
            print(f"[Attempt {attempt}] Connection error: {e}, retrying...")

        delay = min(max_delay, base_delay * (1.3 ** attempt)) # mild exponential growth
        delay = delay * random.uniform(0.7, 1.3)  # jitter so retries desync across users
        time.sleep(delay)

    raise RuntimeError(f"Exceeded {max_retries} retries against {url}")


def get_csrf_token(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    field = soup.find('input', {'name': 'CSRF_TOKEN'})
    if not field or not field.get('value'):
        raise ValueError("Could not find CSRF token in page — page structure may have changed, "
                          "or we got a login/error page instead of the expected one.")
    return field['value']


def looks_logged_out(html_text):
    """Heuristic check: did we get bounced back to a login/session-expired page?"""
    lowered = html_text.lower()
    return ("login" in lowered and "password" in lowered) or "session expired" in lowered


def main():
    client = requests.Session()

    print("Fetching login page for CSRF token...")
    login_page = request_with_retry(client.get, LOGIN_URL, headers=HEADERS, verify=False)
    csrf_token = get_csrf_token(login_page.text)
    print("Got CSRF token.")

    username = input("Enter your USERNAME: ")
    password = getpass.getpass("Enter Password: ")

    login_payload = {
        "username": username,
        "password": password,
        "CSRF_TOKEN": csrf_token
    }

    print("Logging in...")
    login_response = request_with_retry(client.post, LOGIN_URL, data=login_payload, headers=HEADERS, verify=False)

    if "Dashboard" in login_response.text or "Welcome" in login_response.text:
        print("Login successful.")
    else:
        print("Warning: login response didn't contain expected markers. Continuing anyway, "
              "but if this fails, double check your credentials.")

    semId = input("Enter the semester ID you want to fetch result for: ")

    print("Fetching results page (for a fresh CSRF token)...")
    results_page_get = request_with_retry(client.get, RESULT_PAGE_URL, headers=HEADERS, verify=False)

    if looks_logged_out(results_page_get.text):
        raise RuntimeError("Session appears to have been logged out before we could fetch results. "
                            "Try re-running — session/token may have expired during the wait.")

    results_csrf_token = get_csrf_token(results_page_get.text)
    print("Got fresh CSRF token for results form.")

    result_payload = {
        "CSRF_TOKEN": results_csrf_token,
        "form_name": "semesterGradeCardListingSearchForm",
        "semesterId": semId,
        "stdId": "",
        "search": "Search"
    }

    print("Submitting results request (this is the one likely to 504 — will retry automatically)...")
    result_response = request_with_retry(client.post, RESULT_PAGE_URL, data=result_payload,
                                          headers=HEADERS, verify=False, max_retries=100)

    if looks_logged_out(result_response.text):
        raise RuntimeError("Got bounced to a login page on the results POST — session likely expired "
                            "mid-retry. Re-run the script.")

    file_name = f"{username}_{semId}_gradecard.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(result_response.text)
    print(f"Saved raw response to {file_name}")

    print("\n__________ Your Results ___________")
    soup_grades = BeautifulSoup(result_response.text, 'html.parser')
    grades_table = soup_grades.find('table', {'class': 'table-bordered'})

    if grades_table:
        for row in grades_table.find_all('tr'):
            cols = row.find_all('td')
            clean_row = [col.text.strip() for col in cols]
            if clean_row:
                print(" | ".join(clean_row))
    else:
        print("Could not find the grades table. Either results aren't published yet, "
              "or the page structure differs from what's expected — check the saved HTML file.")


if __name__ == "__main__":
    main()