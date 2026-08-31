import os
import requests
from colorama import Fore, Style, init

from auth import get_credentials, prompt_save_credentials
from scraper import login, fetch_results, display_and_save

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SUPPORT_URL = "https://prajwal-56.github.io/donate"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _show_rick() -> None:
    print("\n-----------------------------------------------------------------\n")
    try:
        rick_path = os.path.join(_BASE_DIR, "rick_ascii.txt")
        with open(rick_path, "r") as f:
            rick_ascii = f.read()

        init(autoreset=True)
        highlighted_url = Fore.YELLOW + SUPPORT_URL + Style.RESET_ALL + Fore.CYAN
        updated_ascii   = rick_ascii.replace(SUPPORT_URL, highlighted_url)

        print("\n\n")
        print(Fore.CYAN + updated_ascii)
    except FileNotFoundError:
        pass    # rick_ascii.txt missing — not a critical error, just skip it
    print("\n-----------------------------------------------------------------\n")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    try:
        username, password, is_new_account = get_credentials()
    except KeyboardInterrupt:
        print("\nAborted.")
        return

    client = requests.Session()
    login(client, username, password)

    # Only offer to save when the user typed in fresh credentials
    if is_new_account:
        prompt_save_credentials(username, password)

    sem_id = input(
        'Enter the semester ID you want to fetch results for '
        '(just the number — e.g. "2", "3", "4", ...): '
    )

    result_response = fetch_results(client, sem_id)
    display_and_save(result_response, username, sem_id)
    _show_rick()


if __name__ == "__main__":
    main()
