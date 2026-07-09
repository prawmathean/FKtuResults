# FKtuResults
the repo name can be interpreted as **Fetch** Ktu Results or F___ Ktu Results

## What Is This?
A Python script that logs into the [KTU student portal](https://app.ktu.edu.in) and fetches your semester grade card directly in your terminal — no need to fight the slow, often-504-ing website manually.

Results are printed to the console **and** saved as an HTML file so you can open it in a browser for the full formatted view.

---

## Features

- 🔐 Secure login with your KTU credentials (password is never echoed to the terminal)
- 🔄 Auto-retry with jittered backoff — handles KTU's notorious 504 Gateway Timeouts gracefully
- 🗂 Saves the full grade card as an HTML file (`<username>_<semId>_gradecard.html`)
- 📋 Prints a clean table of your results directly in the terminal

---

## Prerequisites

- Python **3.7+**

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

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install requests beautifulsoup4 urllib3
```

| Package | Purpose |
|---|---|
| `requests` | HTTP client — handles login, sessions, and result fetching |
| `beautifulsoup4` | HTML parser — extracts the CSRF token and grades table |
| `urllib3` | Bundled with `requests`; used here to suppress SSL warnings |

---

## Usage

```bash
python3 FetchMyResults.py
```

You will be prompted for:

1. **USERNAME** — your KTU portal username (usually your register number)
2. **Password** — entered securely (**hidden** input, not echoed)
3. **Semester ID** — the ID of the semester whose results you want

### Finding your Semester ID

The semester ID is a numeric value used internally by the KTU portal. You can find it by:
1. Logging into [app.ktu.edu.in](https://app.ktu.edu.in) in a browser
2. Navigating to **Results → Semester Grade Card**
3. Inspecting the URL or the form's dropdown — the value next to each semester name is the ID

---

## Example Session

```
Fetching login page for CSRF token...
Got CSRF token.
Enter your USERNAME: KTU21CS001
Enter Password:
Logging in...
Login successful.
Enter the semester ID you want to fetch result for: 1801
Fetching results page (for a fresh CSRF token)...
Got fresh CSRF token for results form.
Submitting results request (this is the one likely to 504 — will retry automatically)...
Saved raw response to KTU21CS001_1801_gradecard.html

__________ Your Results ___________
CS301 | Data Structures | S | 10
CS302 | Operating Systems | A+ | 9
...
```

If the KTU server is overloaded, the script will automatically retry (up to 100 times for the results POST) with randomised delays — just leave it running.

---

## Output

| File | Description |
|---|---|
| `<username>_<semId>_gradecard.html` | Full raw HTML response from the portal |


Open the saved HTML file in any browser for the full, formatted grade card view.
(you might've to scroll down a bit inorder to see the actual table of your results)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **"Could not find CSRF token"** | The portal may be down or returning an error page. Wait a moment and retry. |
| **"Session appears to have been logged out"** | The session expired mid-retry. Re-run the script. |
| **"Could not find the grades table"** | Results may not be published yet for that semester, or the portal page structure has changed. Check the saved HTML file manually. |
| **SSL warnings in output** | Expected — the script suppresses KTU's self-signed certificate warnings automatically. |
| **Retrying for a long time** | KTU's servers 504 heavily during peak result-release times. The script will keep retrying; just be patient. |

---

## Notes

- This script uses `verify=False` for SSL because the KTU portal uses a self-signed certificate. This is safe for this specific use case but means certificate authenticity is not verified.
- Credentials are never stored to disk — they only live in memory for the duration of the script.
