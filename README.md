# TKT Outreach Console

Internal campaign management tool for **TKT Church Online Campus**.  
Send personalised Email and WhatsApp messages to contacts from a spreadsheet.

---

## Requirements

| Dependency | Version |
|---|---|
| Docker | 20.10 + |
| Docker Engine running | — |
| Gmail account with App Password | — |
| WhatsApp account (for WA blasts) | — |

> Docker is the only thing you need installed on the host. Everything else runs inside the container.

---

## Project Structure

```
church-sys/
├── app/
│   ├── main.py               # Flask routes
│   ├── email_sender.py       # Gmail / yagmail logic
│   ├── whatsapp_sender.py    # Selenium / WhatsApp Web automation
│   ├── static/
│   │   └── tkt-logo.png      # TKT Church logo (served at /static/)
│   └── templates/
│       └── index.html        # Single-page UI
├── chrome_profile/           # WhatsApp session (persists between runs)
├── images/                   # Uploaded flyer images
├── uploads/                  # Uploaded contact spreadsheets
├── logs/                     # App logs
├── .env                      # Secrets — never commit this file
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── start.sh                  # Quick start script
└── stop.sh                   # Quick stop script
```

---

## First-Time Setup

### 1. Clone / copy the project folder

```bash
cd /home/user/Documents/church-sys
```

### 2. Create the `.env` file

```bash
cp .env.example .env   # if example exists, otherwise create manually
```

Edit `.env`:

```env
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
IMAGE_PATH=/tmp/images/church_flyer.jpeg
```

> `SENDER_PASSWORD` must be a Gmail **App Password**, not your regular password.  
> See the `(i)` button next to the App Password field in the UI for step-by-step instructions.

### 3. Create Docker volumes (one time only)

```bash
docker volume create church_chrome
docker volume create church_images
```

---

## Starting the App

```bash
./start.sh
```

This will:
1. Build the Docker image
2. Stop any previous container
3. Start a fresh container on port **5000**

Then open: **http://localhost:5000**

---

## Stopping the App

```bash
./stop.sh
```

---

## Using Docker Compose (alternative)

```bash
# Start
docker compose up --build -d

# Stop
docker compose down
```

---

## Workflow

| Step | What you do |
|---|---|
| **1 — Upload** | Drop a `.xlsx`, `.xls`, or `.csv` file with columns: `Name`, `Email`, `Number`, `Place`, `Country`, `Continent` |
| **2 — Channel** | Choose **Email** or **WhatsApp** |
| **3 — Compose** | Fill in sender details, subject, message body, optional flyer image and document |
| **4 — Send** | Watch real-time progress per contact. Download CSV report when done. |

Use `{first_name}` anywhere in the subject or body to personalise the message.

---

## WhatsApp Notes

- Click **Connect WhatsApp** to launch WhatsApp Web inside the container.
- Scan the QR code with your phone once.
- Your session is saved in the `church_chrome` Docker volume — **you will not need to scan again** on subsequent runs as long as the volume exists.
- To force a fresh login: click **Reset session** in the UI, or run `docker volume rm church_chrome && docker volume create church_chrome`.

---

## Email Notes

- Uses **Gmail SMTP** via yagmail.
- Requires a **Gmail App Password** (not your main password).
- Optional flyer image is embedded inline (resized to 600×600 JPEG automatically).
- Optional document attachment supports PDF, XLSX, XLS, CSV.

---

## Viewing Live Logs

```bash
docker logs -f church-test
```

Every step of WhatsApp automation is logged in detail (contact name, DOM state, file inputs, send status).

---

## Live Chrome View (WhatsApp debug)

While a WhatsApp session is active, open a second tab:

```
http://localhost:5000/debug
```

This streams a live screenshot of what the browser inside the container sees — useful for diagnosing stuck sessions.

---

## Updating the App

```bash
./stop.sh
./start.sh
```

The image is rebuilt automatically on each `start.sh` run.

---

## Secrets & Security

- **Never commit `.env`** — it contains your Gmail App Password.
- The `church_chrome` volume contains your WhatsApp session cookie. Keep the host machine secure.
- This tool is for **internal use only** — do not expose port 5000 to the public internet without adding authentication.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| WhatsApp QR not appearing | Wait 15 seconds, check `/debug` view, click Reset and try again |
| Image sent as sticker | Should not happen — the automation clicks "Photos & videos" before attaching |
| Gmail authentication error | Ensure App Password is correct and 2-Step Verification is enabled |
| Container won't start | Run `docker logs church-test` to see the error |
| Port 5000 already in use | Run `./stop.sh` first, or change `-p 5000:5000` to `-p 5001:5000` in `start.sh` |
