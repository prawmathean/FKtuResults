import random
import time

import requests
import urllib3
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

LOGIN_URL       = "https://app.ktu.edu.in/login.htm"
RESULT_PAGE_URL = "https://app.ktu.edu.in/eu/res/semesterGradeCardListing.htm"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# S/A+ = bright green, A/B+ = green, B/C+/C/P = yellow, D = red, F/FE = bright red
_GRADE_COLORS = {
    "S":  Fore.GREEN + Style.BRIGHT,
    "A+": Fore.GREEN + Style.BRIGHT,
    "A":  Fore.GREEN,
    "B+": Fore.GREEN,
    "B":  Fore.YELLOW,
    "C+": Fore.YELLOW,
    "C":  Fore.YELLOW,
    "D":  Fore.RED,
    "P":  Fore.YELLOW,
    "F":  Fore.RED + Style.BRIGHT,
    "FE": Fore.RED + Style.BRIGHT,
    "I":  Fore.YELLOW,
}


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

def _info(msg: str) -> None:
    print(Fore.CYAN + "  " + msg)

def _ok(msg: str) -> None:
    print(Fore.GREEN + "  " + msg)

def _warn(msg: str) -> None:
    print(Fore.YELLOW + "  " + msg)

def _retry_msg(attempt: int, reason: str) -> None:
    print(Fore.YELLOW + f"  [{attempt}] {reason}, retrying...")


def _request_with_retry(method, url, max_retries=50, base_delay=3, max_delay=15, **kwargs):
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
            _retry_msg(attempt, f"HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            _retry_msg(attempt, "Timed out")
        except requests.exceptions.RequestException as e:
            _retry_msg(attempt, f"Connection error: {e}")

        delay = min(max_delay, base_delay * (1.3 ** attempt))  # mild exponential growth
        delay *= random.uniform(0.7, 1.3)                      # jitter so retries desync across users
        time.sleep(delay)

    raise RuntimeError(f"Exceeded {max_retries} retries against {url}")


def _get_csrf_token(html_text: str) -> str:
    soup  = BeautifulSoup(html_text, "html.parser")
    field = soup.find("input", {"name": "CSRF_TOKEN"})
    if not field or not field.get("value"):
        raise ValueError(
            "Could not find CSRF token in page. The portal may be down or its structure changed.\n"
            "  Report this at: https://prajwal-56.github.io/contact"
        )
    return field["value"]


def _looks_logged_out(html_text: str) -> bool:
    """Heuristic: did we get bounced back to a login/session-expired page?"""
    lowered = html_text.lower()
    return ("login" in lowered and "password" in lowered) or "session expired" in lowered


def _color_grade(grade: str) -> str:
    color = _GRADE_COLORS.get(grade.strip().upper(), Fore.WHITE)
    return color + grade + Style.RESET_ALL


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def login(client: requests.Session, username: str, password: str) -> None:
    """Fetch the login page, grab a CSRF token, and log in."""
    _info("Connecting to KTU portal...")
    login_page = _request_with_retry(client.get, LOGIN_URL, headers=HEADERS, verify=False)
    csrf_token = _get_csrf_token(login_page.text)

    login_payload = {
        "username":   username,
        "password":   password,
        "CSRF_TOKEN": csrf_token,
    }

    _info("Logging in...")
    login_response = _request_with_retry(
        client.post, LOGIN_URL,
        data=login_payload, headers=HEADERS, verify=False
    )

    if "Dashboard" in login_response.text or "Welcome" in login_response.text:
        _ok("Login successful.")
    else:
        _warn(
            "Login response didn't contain expected markers. Continuing anyway, "
            "but double-check your credentials if this fails."
        )


def fetch_results(client: requests.Session, sem_id: str) -> requests.Response:
    """Fetch the grade card for the given semester. Returns the raw response."""
    _info("Fetching results page...")
    results_page = _request_with_retry(client.get, RESULT_PAGE_URL, headers=HEADERS, verify=False)

    if _looks_logged_out(results_page.text):
        raise RuntimeError(
            "Session was logged out before results could be fetched. Re-run the script."
        )

    results_csrf = _get_csrf_token(results_page.text)

    result_payload = {
        "CSRF_TOKEN": results_csrf,
        "form_name":  "semesterGradeCardListingSearchForm",
        "semesterId": sem_id,
        "stdId":      "",
        "search":     "Search",
    }

    _info("Submitting results request (will auto-retry if the server 504s)...")
    result_response = _request_with_retry(
        client.post, RESULT_PAGE_URL,
        data=result_payload, headers=HEADERS,
        verify=False, max_retries=100
    )

    if _looks_logged_out(result_response.text):
        raise RuntimeError(
            "Got bounced to a login page mid-retry. Session likely expired. Re-run the script."
        )

    return result_response


def display_and_save(result_response: requests.Response, username: str, sem_id: str) -> None:
    """Save the raw HTML to a file and print a formatted results table."""
    file_name = f"{username}_{sem_id}_gradecard.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(result_response.text)

    soup         = BeautifulSoup(result_response.text, "html.parser")
    grades_table = soup.find("table", {"class": "table-bordered"})

    print()
    print(Fore.CYAN + Style.BRIGHT + "  " + "=" * 62)
    print(Fore.CYAN + Style.BRIGHT + f"   Results for {username}  |  Semester {sem_id}")
    print(Fore.CYAN + Style.BRIGHT + "  " + "=" * 62)

    if not grades_table:
        print()
        print(Fore.YELLOW + "  Results not found in the response.")
        print(Fore.YELLOW + "  Either results aren't published yet for this semester,")
        print(Fore.YELLOW + "  or the portal structure changed.")
        print()
        print(Fore.CYAN + f"  Raw response saved to: {file_name}")
        print(Fore.CYAN + "  Open it in a browser to check what came back.")
        return

    all_rows = grades_table.find_all("tr")
    if not all_rows:
        return

    headers   = [th.text.strip() for th in all_rows[0].find_all(["th", "td"])]
    data_rows = all_rows[1:]

    # Split into subject rows (5 cols) and summary rows (2 cols: SGPA, credits etc.)
    subject_rows = []
    summary_rows = []
    for row in data_rows:
        cells = [td.text.strip() for td in row.find_all("td")]
        if not cells:
            continue
        if len(cells) >= 5:
            subject_rows.append(cells)
        else:
            summary_rows.append(cells)

    # Compute column widths from actual data, not just headers
    num_cols   = len(headers)
    col_widths = [len(h) for h in headers]
    for cells in subject_rows:
        for i, cell in enumerate(cells[:num_cols]):
            col_widths[i] = max(col_widths[i], len(cell))

    # Small padding margin on every column
    col_widths  = [w + 2 for w in col_widths]
    total_width = sum(col_widths) + 3 * (num_cols - 1)   # " | " = 3 chars
    divider     = "  " + "-" * total_width

    # ---- Header row -------------------------------------------------------- #
    print()
    header_parts = []
    for h, w in zip(headers, col_widths):
        # pad based on raw text length only
        header_parts.append(Fore.WHITE + Style.BRIGHT + h + " " * (w - len(h)))
    print("  " + (Style.RESET_ALL + Fore.CYAN + " | " + Fore.WHITE + Style.BRIGHT).join(header_parts) + Style.RESET_ALL)
    print(Fore.CYAN + divider)

    # ---- Subject rows ------------------------------------------------------ #
    for cells in subject_rows:
        parts = []
        for i, cell in enumerate(cells[:num_cols]):
            w = col_widths[i]
            padding = " " * max(0, w - len(cell))

            if i == 0:
                colored = Fore.WHITE + Style.BRIGHT + cell   # course name
            elif i == 1:
                colored = Fore.CYAN + Style.BRIGHT + cell    # course code
            elif cell.upper() in _GRADE_COLORS:
                colored = _color_grade(cell)                 # grade
            else:
                colored = Fore.WHITE + cell                  # credits, exam date

            parts.append(colored + padding + Style.RESET_ALL)

        print("  " + (Fore.CYAN + " | " + Style.RESET_ALL).join(parts))

    # ---- Summary rows (credits, SGPA, CGPA) -------------------------------- #
    print(Fore.CYAN + divider)
    for cells in summary_rows:
        if len(cells) >= 2:
            label = cells[0]
            value = cells[1]
            if "SGPA" in label or "CGPA" in label:
                val_colored = Fore.YELLOW + Style.BRIGHT + value
            else:
                val_colored = Fore.WHITE + value
            print(f"  {Fore.WHITE}{label:<35}{Style.RESET_ALL}  {val_colored}{Style.RESET_ALL}")

    print()
    print(Fore.CYAN + "  " + "=" * 62)
    print(Fore.GREEN + f"  Saved full grade card to: {file_name}")
    print(Fore.CYAN + "  " + "=" * 62)
