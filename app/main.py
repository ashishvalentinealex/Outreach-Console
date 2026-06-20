import os
import sys
import uuid
import queue
import threading
import json
import logging

from flask import Flask, request, jsonify, render_template, Response
from werkzeug.utils import secure_filename
import pandas as pd
from dotenv import load_dotenv

from .paths import DATA_DIR, UPLOADS_DIR, IMAGES_DIR, DOCUMENTS_DIR
from .email_sender import send_emails
from .whatsapp_sender import WhatsAppSender

load_dotenv(DATA_DIR / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Resolve template/static dirs so Flask finds them when frozen by PyInstaller
if getattr(sys, 'frozen', False):
    _app_dir = os.path.join(sys._MEIPASS, 'app')
    app = Flask(__name__,
                template_folder=os.path.join(_app_dir, 'templates'),
                static_folder=os.path.join(_app_dir, 'static'))
else:
    app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = str(UPLOADS_DIR)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# In-memory job store: job_id -> {status, progress, total, log, queue}
_jobs: dict = {}
_wa_sender: WhatsAppSender | None = None
_wa_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_df(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath) if filepath.endswith(".csv") else pd.read_excel(filepath)
    df.columns = [c.strip() for c in df.columns]
    return df


def _new_job(total: int) -> tuple[str, queue.Queue]:
    job_id = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()
    _jobs[job_id] = {"status": "running", "progress": 0, "total": total, "log": [], "queue": q}
    return job_id, q


def _finish_job(job_id: str, q: queue.Queue):
    _jobs[job_id]["status"] = "done"
    q.put({"done": True})


# ---------------------------------------------------------------------------
# Routes – pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Routes – file upload
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file provided"}), 400

    filename = secure_filename(f.filename)
    if not filename.endswith((".xlsx", ".xls", ".csv")):
        return jsonify({"error": "Only .xlsx, .xls, or .csv files are supported"}), 400

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(path)

    try:
        df = _load_df(path)
        return jsonify({
            "filepath": path,
            "columns": list(df.columns),
            "total": len(df),
            "preview": df.head(5).fillna("").to_dict("records"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/upload/image", methods=["POST"])
def upload_image():
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "No image provided"}), 400
    filename = secure_filename(f.filename)
    path = os.path.join(str(IMAGES_DIR), filename)
    f.save(path)
    return jsonify({"image_path": path})


@app.route("/upload/document", methods=["POST"])
def upload_document():
    f = request.files.get("document")
    if not f:
        return jsonify({"error": "No document provided"}), 400
    filename = secure_filename(f.filename)
    if not filename.lower().endswith((".pdf", ".xlsx", ".xls", ".csv")):
        return jsonify({"error": "Only PDF, XLSX, XLS, or CSV files are supported"}), 400
    path = os.path.join(str(DOCUMENTS_DIR), filename)
    f.save(path)
    return jsonify({"doc_path": path})


# ---------------------------------------------------------------------------
# Routes – Email
# ---------------------------------------------------------------------------

@app.route("/send/email", methods=["POST"])
def start_email():
    data = request.json or {}
    filepath = data.get("filepath")
    message = data.get("message", "")
    subject = data.get("subject", "Message for {first_name}")
    sender = data.get("sender") or os.getenv("SENDER_EMAIL", "")
    password = data.get("password") or os.getenv("SENDER_PASSWORD", "")
    image_path = data.get("image_path") or os.getenv("IMAGE_PATH", "")
    doc_path = data.get("doc_path", "")

    if not filepath or not sender or not password:
        return jsonify({"error": "Missing filepath, sender email, or password"}), 400

    try:
        df = _load_df(filepath)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    job_id, q = _new_job(len(df))

    def _callback(email, name, success, msg):
        entry = {"identifier": email, "name": name, "success": success, "msg": msg}
        _jobs[job_id]["log"].append(entry)
        _jobs[job_id]["progress"] += 1
        q.put(entry)

    def _run():
        send_emails(df, message, subject, sender, password, image_path, _callback, doc_path)
        _finish_job(job_id, q)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"job_id": job_id})


# ---------------------------------------------------------------------------
# Routes – WhatsApp
# ---------------------------------------------------------------------------

@app.route("/wa/start", methods=["POST"])
def wa_start():
    global _wa_sender
    try:
        with _wa_lock:
            if _wa_sender is None:
                _wa_sender = WhatsAppSender()
            _wa_sender.start()
        return jsonify({"status": "started"})
    except Exception as e:
        logger.error("Failed to start WhatsApp: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/wa/qr")
def wa_qr():
    global _wa_sender
    if _wa_sender is None:
        return jsonify({"logged_in": False, "image": None})
    return jsonify(_wa_sender.get_qr_screenshot())


@app.route("/debug")
def debug_view():
    return """<!DOCTYPE html>
<html>
<head>
  <title>Live WhatsApp View</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0f172a; font-family: sans-serif; display: flex;
           flex-direction: column; align-items: center; min-height: 100vh; }
    .bar { width:100%; background:#1e293b; border-bottom:2px solid #2563eb;
           padding:10px 20px; display:flex; align-items:center; gap:12px; }
    .bar h2 { color:#93c5fd; font-size:15px; }
    .dot { width:10px; height:10px; border-radius:50%; background:#ef4444;
           animation: pulse 1s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
    #status { color:#475569; font-size:12px; margin-left:auto; }
    #screen { max-width:100%; max-height:calc(100vh - 52px);
              display:block; object-fit:contain; }
  </style>
</head>
<body>
  <div class="bar">
    <div class="dot"></div>
    <h2>Live Chrome — WhatsApp Web</h2>
    <span id="status">connecting…</span>
  </div>
  <img id="screen" src="/debug/screenshot" alt="Chrome screen">
  <script>
    let n = 0;
    setInterval(() => {
      n++;
      const img = new Image();
      img.onload = () => {
        document.getElementById('screen').src = img.src;
        document.getElementById('status').textContent = 'frame ' + n;
      };
      img.src = '/debug/screenshot?t=' + n;
    }, 800);
  </script>
</body>
</html>"""


@app.route("/debug/screenshot")
def debug_screenshot():
    global _wa_sender
    if _wa_sender and _wa_sender.driver:
        try:
            png = _wa_sender.driver.get_screenshot_as_png()
            if png:
                return Response(png, mimetype="image/png")
        except Exception as e:
            logger.warning("debug screenshot failed: %s", e)
    # Return a tiny valid grey PNG so the browser doesn't show a broken image icon
    from PIL import Image as _Image
    from io import BytesIO as _BytesIO
    buf = _BytesIO()
    _Image.new("RGB", (1280, 900), (30, 30, 35)).save(buf, format="PNG")
    return Response(buf.getvalue(), mimetype="image/png")


@app.route("/wa/reset", methods=["POST"])
def wa_reset():
    global _wa_sender
    try:
        with _wa_lock:
            if _wa_sender:
                _wa_sender.quit()
            _wa_sender = None
        return jsonify({"status": "reset"})
    except Exception as e:
        logger.error("Failed to reset WhatsApp: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/send/whatsapp", methods=["POST"])
def start_whatsapp():
    global _wa_sender
    data = request.json or {}
    filepath = data.get("filepath")
    message = data.get("message", "")
    image_path = data.get("image_path", "")
    use_number = data.get("use_number", True)

    if not filepath:
        return jsonify({"error": "Missing filepath"}), 400
    if _wa_sender is None or not _wa_sender.is_logged_in():
        return jsonify({"error": "WhatsApp not connected. Please scan the QR code first."}), 400

    try:
        df = _load_df(filepath)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    job_id, q = _new_job(len(df))

    def _callback(name, number, success, msg):
        entry = {"identifier": number or name, "name": name, "success": success, "msg": msg}
        _jobs[job_id]["log"].append(entry)
        _jobs[job_id]["progress"] += 1
        q.put(entry)

    def _run():
        _wa_sender.send_messages(df, message, image_path, None, use_number, _callback)
        _finish_job(job_id, q)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"job_id": job_id})


# ---------------------------------------------------------------------------
# Routes – job progress (SSE)
# ---------------------------------------------------------------------------

@app.route("/progress/<job_id>")
def progress_stream(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    def _generate():
        q = job["queue"]
        while True:
            try:
                entry = q.get(timeout=30)
                yield f"data: {json.dumps(entry)}\n\n"
                if entry.get("done"):
                    break
            except queue.Empty:
                if job["status"] == "done":
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                yield "data: {\"heartbeat\": true}\n\n"

    return Response(_generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/job/<job_id>")
def job_status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Not found"}), 404
    return jsonify({k: v for k, v in job.items() if k != "queue"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
