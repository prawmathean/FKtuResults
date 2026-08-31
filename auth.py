import json
import os
import keyring
import questionary
from questionary import Separator
from colorama import Fore, Style, init

init(autoreset=True)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
USERS_FILE   = os.path.join(_BASE_DIR, "users.json")
SERVICE_NAME = "ktu_results"
_ADD_NEW     = "+ Add new account"


# --------------------------------------------------------------------------- #
# Private helpers  (internal use only)
# --------------------------------------------------------------------------- #

def _load_saved_usernames() -> list[str]:
    """Read the list of saved usernames from users.json."""
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _append_username(username: str) -> None:
    """Add a username to users.json (no duplicates)."""
    usernames = _load_saved_usernames()
    if username not in usernames:
        usernames.append(username)
        with open(USERS_FILE, "w") as f:
            json.dump(usernames, f, indent=2)


def _keyring_save(username: str, password: str) -> bool:
    """Save password to the OS keyring. Returns True on success."""
    try:
        keyring.set_password(SERVICE_NAME, username, password)
        return True
    except Exception:
        return False


def _keyring_load(username: str) -> str | None:
    """Fetch password from the OS keyring. Returns None on failure."""
    try:
        return keyring.get_password(SERVICE_NAME, username)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def get_credentials() -> tuple[str, str, bool]:
    """
    Show the account-selection menu (if saved accounts exist) or prompt for
    fresh credentials.

    Returns:
        (username, password, is_new_account)
        is_new_account is True when the user typed in fresh credentials.
    """
    saved_usernames = _load_saved_usernames()

    if saved_usernames:
        choices = saved_usernames + [Separator(), _ADD_NEW]

        selected = questionary.select(
            "Who are you logging in as?",
            choices=choices
        ).ask()

        if selected is None:
            raise KeyboardInterrupt

        if selected != _ADD_NEW:
            password = _keyring_load(selected)
            if password is not None:
                print(Fore.GREEN + f"  Loaded saved credentials for {selected}.")
                return selected, password, False

            # Keyring returned nothing (password deleted externally, etc.)
            print(Fore.YELLOW + f"  No saved password found for '{selected}'. Enter it manually.")
            password = questionary.password("Password:").ask()
            return selected, password, True

    # No saved accounts or user chose to add a new one
    username = questionary.text("KTU Username:").ask()
    password = questionary.password("Password:").ask()
    return username, password, True


def prompt_save_credentials(username: str, password: str) -> None:
    """
    Ask the user if they want to save credentials for next time.
    Call this only when the user entered fresh credentials.

    To remove an account manually:
      1. Delete the username entry from users.json
      2. Run:  python -c "import keyring; keyring.delete_password('ktu_results', 'USERNAME')"
    """
    try:
        save = questionary.confirm(
            "Save this login for next time?",
            default=False
        ).ask()

        if not save:
            return

        if _keyring_save(username, password):
            _append_username(username)
            print(Fore.GREEN + "  Saved. Your password is stored in your system keyring.")
        else:
            print(Fore.YELLOW + "  Keyring not available on this machine. Login was not saved.")

    except Exception:
        pass  # Never let saving crash the main script
