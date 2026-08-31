import json
import os
import keyring
import questionary
from questionary import Separator

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
USERS_FILE   = os.path.join(_BASE_DIR, "users.json")
SERVICE_NAME = "ktu_results"
_ADD_NEW     = "+ Add new account"


# --------------------------------------------------------------------------- #
# Private helpers  (internal use only — don't import these elsewhere)
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
        is_new_account is True when the user typed in fresh credentials,
        False when loaded from a saved account.
    """
    saved_usernames = _load_saved_usernames()

    if saved_usernames:
        # Build the menu: saved accounts first, then a separator, then the
        # "add new" option at the bottom.
        choices = saved_usernames + [Separator(), _ADD_NEW]

        selected = questionary.select(
            "Who are you logging in as?",
            choices=choices
        ).ask()

        if selected is None:           # user hit Ctrl+C
            raise KeyboardInterrupt

        if selected != _ADD_NEW:
            # --- Existing account selected ---
            password = _keyring_load(selected)
            if password is not None:
                print(f"  Loaded saved credentials for {selected}.")
                return selected, password, False

            # Keyring returned nothing (e.g. password was deleted externally)
            print(f"  Couldn't find a saved password for '{selected}'. Enter it manually.")
            password = questionary.password("Enter Password:").ask()
            return selected, password, True   # treat as new so we offer to re-save

    # --- No saved accounts, or user chose "+ Add new account" ---
    username = questionary.text("Enter KTU Username:").ask()
    password = questionary.password("Enter Password:").ask()
    return username, password, True


def prompt_save_credentials(username: str, password: str) -> None:
    """
    Ask the user if they want to save their credentials for next time.
    Call this only after the user has entered fresh credentials.

    To manually remove an account later:
      1. Delete the username from users.json
      2. Run in a Python shell:
           import keyring
           keyring.delete_password("ktu_results", "<username>")
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
            print("  Saved! Your credentials are stored securely in your system keyring.")
        else:
            print("  Couldn't access the system keyring on this machine — login was not saved.")

    except Exception:
        # Saving is a nice-to-have. Never let it crash the main script.
        pass
