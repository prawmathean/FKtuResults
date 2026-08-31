import os
import requests
import questionary
from colorama import Fore, Style, init

from auth import get_credentials, prompt_save_credentials
from scraper import login, fetch_results, display_and_save

init(autoreset=True)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SUPPORT_URL = "https://prajwal-56.github.io/donate"

_BANNER = f"""
{Fore.CYAN + Style.BRIGHT}  ┌─────────────────────────────────────────────┐
  │          KTU Result Fetcher                 │
  │    Fights the 504 so you don't have to      │
  │                                             │
  │    Handcrafted by Prajwal (prawmathean)     │
  └─────────────────────────────────────────────┘{Style.RESET_ALL}
"""

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _show_support() -> None:
    """Print the support section at the end."""
    print()
    print(Fore.CYAN + "  " + "─" * 50)

    try:
        rick_path = os.path.join(_BASE_DIR, "rick_ascii.txt")
        with open(rick_path, "r") as f:
            rick_ascii = f.read()

        highlighted_url = Fore.YELLOW + Style.BRIGHT + SUPPORT_URL + Style.RESET_ALL + Fore.CYAN
        updated_ascii   = rick_ascii.replace(SUPPORT_URL, highlighted_url)
        print(Fore.CYAN + updated_ascii)
    except FileNotFoundError:
        # ascii file missing, just show a plain support line
        print(Fore.CYAN + f"\n  Support the project: " + Fore.YELLOW + Style.BRIGHT + SUPPORT_URL)

    print(Fore.CYAN + "  " + "─" * 50)
    print()


def _pick_semester() -> str:
    """Prompt for a semester number using questionary."""
    sem = questionary.text(
        "Which semester?",
        instruction="(enter the number, e.g. 4)",
        validate=lambda val: True if val.strip().isdigit() else "Please enter a number"
    ).ask()

    if sem is None:
        raise KeyboardInterrupt

    return sem.strip()


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    print(_BANNER)

    try:
        username, password, is_new_account = get_credentials()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n  Aborted.")
        return

    print()
    client = requests.Session()
    login(client, username, password)

    if is_new_account:
        print()
        prompt_save_credentials(username, password)

    print()

    try:
        sem_id = _pick_semester()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n  Aborted.")
        return

    print()
    result_response = fetch_results(client, sem_id)
    display_and_save(result_response, username, sem_id)
    _show_support()


if __name__ == "__main__":
    main()
