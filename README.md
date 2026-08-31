# FKtuResults
the repo name can be interpreted as **Fetch** Ktu Results or F___ Ktu Results

## What Is This?
A Python script that logs into the [KTU student portal](https://app.ktu.edu.in) and fetches your semester grade card directly in your terminal — no need to fight the slow, often-504-ing website manually.

Results are printed to the console **and** saved as an HTML file so you can open it in a browser for the full formatted view.

---

## Features

- 🔐 Secure login with your KTU credentials (password is never echoed to the terminal)
- 💾 Save your login so you don't have to type it in every time
- 🔄 Auto-retry with jittered backoff — handles KTU's notorious 504 Gateway Timeouts gracefully
- 🗂 Saves the full grade card as an HTML file (`<username>_<semId>_gradecard.html`)
- 📋 Prints a clean table of your results directly in the terminal

---

## Prerequisites

- Python **3.10+**

Check your version:
```bash
python3 --version
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/prawmathean/FKtuResults.git
cd FKtuResults
```

### 2. (Recommended) Create a virtual environment

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

> You'll need to run the activate command every time you open a new terminal to work on this.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| `requests` | HTTP client — handles login, sessions, and result fetching |
| `beautifulsoup4` | HTML parser — extracts the CSRF token and grades table |
| `urllib3` | Bundled with `requests`; used here to suppress SSL warnings |
| `colorama` | Cross-platform colors for the ASCII art |
| `keyring` | Saves your password securely into the OS credential store |
| `questionary` | The interactive arrow-key selection menu |

---

## Usage

```bash
python FetchMyResults.py
```

### First run (no saved accounts)

You'll be asked to enter your username and password. After logging in, the script will ask if you want to save your login for next time. If you say yes, your password gets stored in your OS's credential store (Windows Credential Manager, macOS Keychain, Linux Secret Service) and your username is saved to a local `users.json` file.

### Next time

You'll see a menu like this instead of being asked to type anything:

```
Who are you logging in as?
> QWE24CS069
  QWE24CS067
  ──────────────────
  + Add new account
```

Navigate with your arrow keys and hit Enter to select.

After that, it'll ask for your semester number and fetch your results.

---

## File Structure

```
FKtuResults/
├── FetchMyResults.py   # entry point, run this
├── auth.py             # handles the login menu and credential storage
├── scraper.py          # everything that talks to the KTU website
├── users.json          # list of saved usernames (auto-created, gitignored)
├── rick_ascii.txt      # you know why
└── requirements.txt
```

---

## Removing a Saved Account

There's no in-app option for this (yet). To remove an account manually:

1. Open `users.json` and delete that username from the list
2. Delete the saved password from your keyring by running this in a terminal:

```bash
python -c "import keyring; keyring.delete_password('ktu_results', 'YOUR_USERNAME')"
```

Replace `YOUR_USERNAME` with the actual username.

---

## Example Session

```
Who are you logging in as?
> KTU21CS001
  + Add new account

  Loaded saved credentials for KTU21CS001.
Fetching login page for CSRF token...
Got CSRF token.
Logging in...
Login successful.
Enter the semester ID you want to fetch result for: 4
...
Saved raw response to KTU21CS001_4_gradecard.html

__________ Your Results ___________
CS301 | Data Structures | S  | 10
CS302 | Operating Systems | A+ | 9
...
```

If the KTU server is overloaded, the script will automatically retry (up to 100 times for the results POST) with random delays. Just leave it running.

---

## Output

| File | Description |
|---|---|
| `<username>_<semId>_gradecard.html` | Full raw HTML response from the portal |

Open the saved HTML file in any browser for the full, formatted grade card view.
(you might have to scroll down a bit to see the actual table)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **"Could not find CSRF token"** | The portal may be down or returning an error page. Wait a bit and retry. |
| **"Session appears to have been logged out"** | The session expired mid-retry. Re-run the script. |
| **"Could not find the grades table"** | Results may not be published yet for that semester, or the portal page structure has changed. Check the saved HTML file manually. |
| **SSL warnings in output** | Expected — the script suppresses KTU's self-signed certificate warnings automatically. |
| **Retrying for a long time** | KTU's servers 504 heavily when results drop. Just be patient. |
| **Saved login not working on this machine** | Some minimal Linux setups (like Termux on Android) don't have a keyring backend. The script will warn you and skip saving. |

---

## Notes

- This script uses `verify=False` for SSL because the KTU portal uses a self-signed certificate. It's fine for this specific use case.
- Your password is stored by the operating system's credential manager, not in any file this script controls.

---

## SUPPORT
If this helped you out or you find it cool, feel free to buy me a coffee: https://prajwal-56.github.io/donate
