import re
import os
import yagmail
from PIL import Image


RESIZED_PATH = "/tmp/TKT_CHURCH.jpeg"


def _resize_image(image_path: str) -> str:
    os.makedirs(os.path.dirname(RESIZED_PATH), exist_ok=True)
    with Image.open(image_path) as im:
        im.thumbnail((600, 600))
        im.save(RESIZED_PATH, format="JPEG")
    return RESIZED_PATH


def _extract_first_name(full_name: str) -> str:
    parts = str(full_name).strip().split()
    if not parts:
        return full_name
    # Skip single-char prefixes like "Dr", "Mr" etc. (len <= 2)
    first = parts[1] if len(parts) > 1 and len(parts[0]) <= 2 else parts[0]
    return first.capitalize()


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def send_emails(df, message_template, subject_template, sender, password, image_path, callback, doc_path=""):
    email_col = next((c for c in df.columns if c.lower() in ("email", "email address")), None)
    name_col = next((c for c in df.columns if c.lower() == "name"), None)

    if not email_col:
        callback("", "", False, "No Email column found in spreadsheet")
        return

    resized = None
    if image_path and os.path.exists(image_path):
        try:
            resized = _resize_image(image_path)
        except Exception as e:
            callback("", "", False, f"Image resize failed: {e}")

    try:
        yag = yagmail.SMTP(user=sender, password=password)
    except Exception as e:
        callback("", "", False, f"SMTP login failed: {e}")
        return

    for _, row in df.iterrows():
        email = str(row[email_col]).strip()
        if not _EMAIL_RE.fullmatch(email):
            callback(email, "", False, "Invalid email address")
            continue

        name = str(row[name_col]).strip() if name_col else email
        first_name = _extract_first_name(name)

        subject = subject_template.format(first_name=first_name)
        body = message_template.format(first_name=first_name)

        try:
            contents = []
            if resized:
                contents.append(yagmail.inline(resized))
            contents.append(body)
            attachments = [doc_path] if doc_path and os.path.exists(doc_path) else []
            yag.send(to=email, subject=subject, contents=contents, attachments=attachments)
            callback(email, first_name, True, "Sent")
        except Exception as e:
            callback(email, first_name, False, str(e))
