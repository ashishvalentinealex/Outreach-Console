# Outreach Console

Internal campaign management tool for **TKT Church Online Campus**.  
Send personalised Email and WhatsApp messages to contacts from a spreadsheet.

---

## Two Ways to Run

| | Native (Recommended) | Docker |
|---|---|---|
| **Who it's for** | Church staff, non-technical users | Developers |
| **Requires** | Chrome browser | Docker |
| **Setup** | Double-click to run | `./start.sh` |
| **Works on** | Windows & Linux | Linux & Mac |

---

## Option A — Native Executable (No Docker, No Python)

The simplest way. Download the executable for your OS, double-click it, and the app opens in your browser automatically.

### Prerequisites
- **Chrome** must be installed (already on most machines)
- Nothing else — Python and Docker are **not** required

### First-Time Setup

**1. Download the executable**

- Linux: `OutreachConsole`
- Windows: `OutreachConsole.exe`

**2. (Optional) Pre-configure credentials**

Create a file called `.env` in `~/OutreachConsole/` (Linux) or `%APPDATA%\OutreachConsole\` (Windows):

```env
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
```

> You can also type these directly in the app UI — the `.env` file is optional.

**3. Run it**

Double-click the executable. A console window appears and your browser opens at `http://localhost:5000` automatically.

### Data Persistence

All your data is stored in a folder on your machine and **survives restarts**:

| OS | Data location |
|---|---|
| Linux | `~/OutreachConsole/` |
| Windows | `%APPDATA%\OutreachConsole\` |

This includes uploaded spreadsheets, flyer images, your WhatsApp session (no need to scan QR again), and logs.

---

## Option B — Docker (Developer / Server)

### Prerequisites

| Dependency | Version |
|---|---|
| Docker | 20.10+ |
| Docker Engine running | — |

### Setup

**1. Clone the repo**

```bash
git clone https://github.com/ashishvalentinealex/Outreach-Console.git
cd Outreach-Console
```

**2. Create the `.env` file**

```bash
cp .env.example .env
```

Edit `.env`:

```env
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
IMAGE_PATH=/tmp/images/church_flyer.jpeg
```

> `SENDER_PASSWORD` must be a Gmail **App Password**, not your regular password.

**3. Start**

```bash
./start.sh
```

Docker volumes are created automatically on first run. Open **http://localhost:5000**.

**4. Stop**

```bash
./stop.sh
```

### Docker Compose (alternative)

```bash
docker compose up --build -d   # start
docker compose down            # stop
```

---

## Building the Executable Yourself

Run these commands on the target OS (Linux or Windows):

**Linux**
```bash
bash build.sh
# Output: dist/OutreachConsole
```

**Windows**
```bat
build.bat
REM Output: dist\OutreachConsole.exe
```

Requires Python 3.11+ on the machine doing the build. The resulting executable has no such requirement.

---

## Project Structure

```
Outreach-Console/
├── app/
│   ├── main.py               # Flask routes
│   ├── email_sender.py       # Gmail / yagmail logic
│   ├── whatsapp_sender.py    # Selenium / WhatsApp Web automation
│   ├── paths.py              # Cross-platform data directory
│   ├── static/
│   │   └── tkt-logo.png
│   └── templates/
│       └── index.html        # Single-page UI
├── launcher.py               # Native entry point (opens browser automatically)
├── OutreachConsole.spec      # PyInstaller build config
├── build.sh                  # Linux build script
├── build.bat                 # Windows build script
├── Dockerfile                # Docker build
├── docker-compose.yml
├── requirements.txt
├── start.sh                  # Docker quick-start
├── stop.sh                   # Docker quick-stop
└── .env.example              # Credentials template
```

---

## Workflow

| Step | What you do |
|---|---|
| **1 — Upload** | Drop a `.xlsx`, `.xls`, or `.csv` file with columns: `Name`, `Email`, `Number` |
| **2 — Channel** | Choose **Email** or **WhatsApp** |
| **3 — Compose** | Fill in sender details, subject, message body, optional flyer image and document |
| **4 — Send** | Watch real-time progress per contact. Download CSV report when done. |

Use `{first_name}` anywhere in the subject or body to personalise the message.

---

## WhatsApp Notes

- Click **Connect WhatsApp** to open a Chrome window with WhatsApp Web.
- Scan the QR code with your phone once.
- Your session is saved locally — **you will not need to scan again** on subsequent runs.
- To force a fresh login: click **Reset session** in the UI.

---

## Email Notes

- Uses **Gmail SMTP** via yagmail.
- Requires a **Gmail App Password** (not your main password).
- Optional flyer image is embedded inline (resized to 600×600 JPEG automatically).
- Optional document attachment supports PDF, XLSX, XLS, CSV.

---

## Viewing Logs

**Native**: logs are written to `~/OutreachConsole/logs/outreach.log`

**Docker**:
```bash
docker logs -f outreach-console
```

---

## Live Chrome View (WhatsApp debug)

While a WhatsApp session is active, open:

```
http://localhost:5000/debug
```

Streams a live screenshot of the Chrome window — useful for diagnosing stuck sessions.

---

## Secrets & Security

- **Never commit `.env`** — it contains your Gmail App Password.
- The `OutreachConsole/chrome_profile` folder contains your WhatsApp session. Keep your machine secure.
- This tool is for **internal use only** — do not expose port 5000 to the public internet without adding authentication.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| WhatsApp QR not appearing | Wait 15 seconds, check `/debug` view, click Reset and try again |
| Gmail authentication error | Ensure App Password is correct and 2-Step Verification is enabled on your Google account |
| Port 5000 already in use | Another app is using port 5000 — close it, or change the port in `launcher.py` and rebuild |
| Chrome not found (native) | Install Google Chrome from [google.com/chrome](https://www.google.com/chrome) |
| Container won't start (Docker) | Run `docker logs outreach-console` to see the error |
