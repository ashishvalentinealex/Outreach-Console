import glob
import os
import re
import time
import base64
import logging
from io import BytesIO
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

CHROME_PROFILE  = "/tmp/chrome_profile"
CHROMEDRIVER    = "/usr/bin/chromedriver"
WA_RESIZED_PATH = "/tmp/TKT_CHURCH.jpeg"

# ── XPATHs taken from live WhatsApp Web HTML ─────────────────────────────────
SEARCH_INPUT  = "//input[@data-tab='3']"
FIRST_RESULT  = "(//span[@dir='auto' and @title])[1]"
MSG_BOX       = "//div[@contenteditable='true' and @data-tab='10'] | //div[@aria-label='Type a message']"
PLUS_BTN      = "//span[@data-testid='plus-rounded']"
# Walk from "Photos & videos" text up to its container, then get the file input inside it
PHOTO_FILE_INPUT = (
    "//span[normalize-space(.)='Photos & videos']"
    "/ancestor::*[.//input[@type='file']][1]//input[@type='file']"
)
SEND_BTN      = "//span[@data-testid='wds-ic-send-filled']"
DISCARD_BTN   = "//button[contains(.,'Discard')]"
LOGGED_IN     = "//div[@aria-label='Chat list'] | //div[@id='side']"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prepare_image(image_path: str) -> str:
    with Image.open(image_path) as im:
        im.thumbnail((800, 800))
        # JPEG doesn't support alpha — convert RGBA/LA/P images to RGB first
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGB")
        im.save(WA_RESIZED_PATH, format="JPEG", quality=90)
    logger.info("Image prepared: %s → %s", image_path, WA_RESIZED_PATH)
    return WA_RESIZED_PATH


def _normalize_phone(number: str) -> str:
    raw = re.sub(r"[\s\+\-\(\)]", "", str(number))
    if raw.startswith("00"):
        raw = raw[2:]
    if raw.startswith("0") and len(raw) == 10:
        raw = "27" + raw[1:]
    if len(raw) == 9 and raw[0] in "678":
        raw = "27" + raw
    return raw


def _extract_first_name(full_name: str) -> str:
    parts = str(full_name).strip().split()
    if not parts:
        return str(full_name)
    first = parts[1] if len(parts) > 1 and len(parts[0]) <= 2 else parts[0]
    return first.capitalize()


def _type_multiline(driver, element, text: str):
    """Type message via JS execCommand — handles emoji and all Unicode (send_keys breaks on non-BMP chars)."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            ActionChains(driver)\
                .key_down(Keys.SHIFT).send_keys(Keys.RETURN)\
                .key_up(Keys.SHIFT).perform()
        if line:
            driver.execute_script(
                "arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",
                element, line
            )


# ── WhatsApp Sender ───────────────────────────────────────────────────────────

class WhatsAppSender:

    def __init__(self):
        self.driver = None
        self._logged_in = False

    # ── Chrome ────────────────────────────────────────────────────────────────

    @staticmethod
    def _clear_locks():
        for name in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            for f in glob.glob(os.path.join(CHROME_PROFILE, name)):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def start(self):
        if self.driver:
            logger.info("Chrome already running — skipping start.")
            return
        logger.info("STEP: Clearing Chrome singleton locks...")
        self._clear_locks()
        logger.info("STEP: Launching Chromium with profile at %s", CHROME_PROFILE)

        opts = webdriver.ChromeOptions()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-software-rasterizer")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        )
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        binary = os.getenv("CHROMIUM_BIN", "/usr/bin/chromium")
        if os.path.exists(binary):
            opts.binary_location = binary

        service = Service(executable_path=CHROMEDRIVER)
        self.driver = webdriver.Chrome(service=service, options=opts)
        logger.info("STEP: Chrome launched. Hiding webdriver flag...")
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
        )
        logger.info("STEP: Navigating to https://web.whatsapp.com/ ...")
        self.driver.get("https://web.whatsapp.com/")
        logger.info("STEP: WhatsApp Web page loaded.")

    def quit(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self._logged_in = False
        self._clear_locks()

    # ── Status / QR ──────────────────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        if self._logged_in:
            return True
        if not self.driver:
            return False
        try:
            self.driver.find_element(By.XPATH, LOGGED_IN)
            self._logged_in = True
            return True
        except NoSuchElementException:
            return False

    def get_qr_screenshot(self) -> dict:
        if not self.driver:
            return {"logged_in": False, "image": None}
        if self.is_logged_in():
            return {"logged_in": True, "image": None}
        try:
            qr_el = self.driver.find_element(By.XPATH, "//canvas | //div[@data-ref]")
            png = qr_el.screenshot_as_png
            img = Image.open(BytesIO(png)).convert("RGB")
            padded = Image.new("RGB", (img.width + 40, img.height + 40), (255, 255, 255))
            padded.paste(img, (20, 20))
            buf = BytesIO()
            padded.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
        except Exception:
            try:
                png = self.driver.get_screenshot_as_png()
                b64 = base64.b64encode(png).decode()
            except Exception as e:
                logger.error("Screenshot failed: %s", e)
                return {"logged_in": False, "image": None}
        return {"logged_in": False, "image": b64}

    def get_full_screenshot_png(self):
        if not self.driver:
            return None
        try:
            return self.driver.get_screenshot_as_png()
        except Exception:
            return None

    # ── Core send steps ───────────────────────────────────────────────────────

    def _clear_search_input(self, search):
        logger.info("STEP: Clearing search input (JS click → Ctrl+A → Delete → JS reset)...")
        self._js_click(search)
        time.sleep(0.2)
        search.send_keys(Keys.CONTROL + 'a')
        time.sleep(0.1)
        search.send_keys(Keys.DELETE)
        time.sleep(0.2)
        self.driver.execute_script("""
            const inp = arguments[0];
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(inp, '');
            inp.dispatchEvent(new Event('input', { bubbles: true }));
        """, search)
        time.sleep(0.2)
        logger.info("STEP: Search input cleared.")

    def _search_contact(self, name: str) -> bool:
        wait = WebDriverWait(self.driver, 15)
        logger.info("[%s] STEP 1: Waiting for search box (data-tab='3')...", name)
        search = wait.until(EC.element_to_be_clickable((By.XPATH, SEARCH_INPUT)))
        logger.info("[%s] STEP 1: Search box found.", name)
        self._clear_search_input(search)
        logger.info("[%s] STEP 1: Typing name into search: '%s'", name, name)
        search.send_keys(name)
        logger.info("[%s] STEP 1: Waiting 2s for results...", name)
        time.sleep(2)

        try:
            first = self.driver.find_element(By.XPATH, FIRST_RESULT)
            logger.info("[%s] STEP 1: First result title='%s'", name, first.get_attribute("title"))
        except Exception:
            no_results = self.driver.execute_script("""
                return document.body.innerText.includes('No chats, contacts or messages found');
            """)
            if no_results:
                logger.warning("[%s] STEP 1: No results found — skipping contact.", name)
                search.clear()
                return False
            logger.warning("[%s] STEP 1: Could not verify first result element — proceeding anyway.", name)

        logger.info("[%s] STEP 1: Pressing Enter to open chat...", name)
        search.send_keys(Keys.ENTER)
        logger.info("[%s] STEP 1: Waiting 2s for chat to open...", name)
        time.sleep(2)
        logger.info("[%s] STEP 1: Chat opened.", name)
        return True

    def _js_click(self, element):
        """Click via JavaScript — bypasses any overlapping element."""
        self.driver.execute_script("arguments[0].click();", element)

    def _dismiss_popups(self):
        logger.info("STEP: Dismissing any open overlays (ESC x2 + discard popup check)...")
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            logger.info("STEP: ESC #1 sent.")
            time.sleep(0.5)
        except Exception as e:
            logger.warning("STEP: ESC #1 failed: %s", e)
        self._dismiss_discard_popup(prefer_cancel=False)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            logger.info("STEP: ESC #2 sent.")
            time.sleep(0.5)
        except Exception as e:
            logger.warning("STEP: ESC #2 failed: %s", e)

    def _clear_search(self):
        logger.info("STEP: Clearing search box for next contact...")
        try:
            search = self.driver.find_element(By.XPATH, SEARCH_INPUT)
            self._clear_search_input(search)
            logger.info("STEP: Search box cleared.")
        except Exception as e:
            logger.warning("STEP: Could not clear search box: %s", e)

    def _send_text(self, name: str, message: str):
        wait = WebDriverWait(self.driver, 15)
        logger.info("[%s] STEP TEXT-1: Waiting for message box (data-tab='10')...", name)
        msg_box = wait.until(EC.element_to_be_clickable((By.XPATH, MSG_BOX)))
        logger.info("[%s] STEP TEXT-1: Message box found — clicking...", name)
        self._js_click(msg_box)
        logger.info("[%s] STEP TEXT-2: Typing message (%d chars)...", name, len(message))
        _type_multiline(self.driver, msg_box, message)
        time.sleep(1)
        logger.info("[%s] STEP TEXT-3: Waiting for send button...", name)
        send = wait.until(EC.presence_of_element_located((By.XPATH, SEND_BTN)))
        logger.info("[%s] STEP TEXT-3: Send button found — clicking...", name)
        self._js_click(send)
        logger.info("[%s] STEP TEXT-3: Text message sent. Waiting 2s...", name)
        time.sleep(2)

    def _dismiss_discard_popup(self, prefer_cancel: bool = False):
        label = "Cancel" if prefer_cancel else "Discard"
        logger.info("STEP: Checking for 'Discard selection?' popup (will click '%s')...", label)
        clicked = self.driver.execute_script("""
            const label = arguments[0];
            const buttons = Array.from(document.querySelectorAll('button'));
            const btn = buttons.find(b => b.textContent.trim() === label);
            if (btn) { btn.click(); return true; }
            return false;
        """, label)
        if clicked:
            logger.info("STEP: 'Discard selection?' popup found and clicked '%s'.", label)
            time.sleep(0.8)
        else:
            logger.info("STEP: No 'Discard selection?' popup present — continuing.")
        return clicked

    def _send_image_only(self, name: str, image_path: str):
        """Send image as a photo with no caption — separate from the text message."""
        wait = WebDriverWait(self.driver, 20)

        logger.info("[%s] STEP IMG-1: Waiting for '+' attach button...", name)
        plus = wait.until(EC.presence_of_element_located((By.XPATH, PLUS_BTN)))
        logger.info("[%s] STEP IMG-1: '+' button found — clicking to open attach menu...", name)
        self._js_click(plus)
        logger.info("[%s] STEP IMG-1: Attach menu opened. Waiting 1.5s...", name)
        time.sleep(1.5)

        # Log file inputs BEFORE clicking Photos & videos
        before = self.driver.execute_script(
            "return Array.from(document.querySelectorAll('input[type=\"file\"]')).map(i => i.accept || '(empty)');"
        )
        logger.info("[%s] STEP IMG-2: File inputs BEFORE clicking Photos: %s", name, before)

        # Click the "Photos & videos" menu item to activate WhatsApp's photo upload state.
        # We dispatch a non-bubbling click so it fires WhatsApp's JS handler without
        # propagating to the label (which would open the OS file dialog).
        logger.info("[%s] STEP IMG-2: Clicking 'Photos & videos' menu item...", name)
        photos_clicked = self.driver.execute_script("""
            for (const el of document.querySelectorAll('span, div, li')) {
                const txt = el.textContent.trim();
                if (txt === 'Photos & videos' || txt === 'Photos & Videos') {
                    el.click();
                    return true;
                }
            }
            return false;
        """)
        logger.info("[%s] STEP IMG-2: 'Photos & videos' click result: %s", name, photos_clicked)
        time.sleep(0.8)

        # Dismiss any Discard popup that appeared
        self._dismiss_discard_popup(prefer_cancel=True)

        # Log file inputs AFTER clicking Photos & videos
        after = self.driver.execute_script(
            "return Array.from(document.querySelectorAll('input[type=\"file\"]')).map(i => i.accept || '(empty)');"
        )
        logger.info("[%s] STEP IMG-2: File inputs AFTER clicking Photos: %s", name, after)

        # Find the most recently added / best-matching file input
        file_input = self.driver.execute_script("""
            const inputs = Array.from(document.querySelectorAll('input[type="file"]'));
            // Prefer one with video types (true Photos & videos input)
            const photos = inputs.find(i => {
                const acc = (i.accept || '').toLowerCase();
                return acc.includes('video/mp4') || acc.includes('video/3gpp') ||
                       acc.includes('video/quicktime') || acc.includes('video/*');
            });
            // Fallback: any that starts with 'image/*,' (not just 'image/*')
            const fallback = photos ? null : inputs.find(i => (i.accept||'').startsWith('image/*,'));
            // Last fallback: the last input in the DOM (newly added ones appear at end)
            return photos || fallback || (inputs.length > 0 ? inputs[inputs.length - 1] : null);
        """)
        if not file_input:
            raise Exception("No file input found in DOM after clicking Photos & videos")
        accept_attr = self.driver.execute_script("return arguments[0].accept;", file_input)
        logger.info("[%s] STEP IMG-2: Using file input with accept='%s' — sending: %s",
                    name, accept_attr, image_path)
        file_input.send_keys(image_path)
        logger.info("[%s] STEP IMG-2: Image path sent. Waiting 3.5s for preview to load...", name)
        time.sleep(3.5)

        self._dismiss_discard_popup(prefer_cancel=True)

        logger.info("[%s] STEP IMG-3: Waiting for send button in image preview...", name)
        send = wait.until(EC.presence_of_element_located((By.XPATH, SEND_BTN)))
        logger.info("[%s] STEP IMG-3: Send button found — clicking...", name)
        self._js_click(send)
        logger.info("[%s] STEP IMG-3: Image sent. Waiting 3s for delivery...", name)
        time.sleep(3)

    def _process_contact(self, name: str, message: str, image_path: str, retries: int = 1):
        if image_path and os.path.exists(image_path):
            logger.info("[%s] Preparing image: %s", name, image_path)
            ready_image = _prepare_image(image_path)
        else:
            logger.info("[%s] No image provided or file not found — text only.", name)
            ready_image = None

        for attempt in range(retries + 1):
            logger.info("[%s] --- Attempt %d of %d ---", name, attempt + 1, retries + 1)
            try:
                self._dismiss_popups()
                found = self._search_contact(name)
                if not found:
                    return False, "Contact not found in WhatsApp"

                if ready_image:
                    logger.info("[%s] Sending image first...", name)
                    self._send_image_only(name, ready_image)
                    logger.info("[%s] Image done. Now sending text...", name)
                else:
                    logger.info("[%s] Sending text only...", name)
                self._send_text(name, message)

                logger.info("[%s] ✓ ALL DONE — image + text sent successfully.", name)
                self._clear_search()
                return True, "Sent"

            except Exception as e:
                logger.warning("[%s] Attempt %d FAILED: %s", name, attempt + 1, e)
                try:
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    logger.info("[%s] ESC sent after failure to close any overlay.", name)
                    time.sleep(1)
                except Exception:
                    pass
                self._clear_search()
                if attempt < retries:
                    logger.info("[%s] Retrying in 2s...", name)
                    time.sleep(2)
                    continue
                logger.error("[%s] ✗ GIVING UP after %d attempt(s): %s", name, retries + 1, e)
                return False, str(e)

    # ── Public entry point ───────────────────────────────────────────────────

    def send_messages(self, df, message_template: str, image_path: str,
                      id_column, use_number: bool, callback):

        if not self.is_logged_in():
            logger.info("Waiting for WhatsApp login...")
            try:
                WebDriverWait(self.driver, 120).until(
                    EC.presence_of_element_located((By.XPATH, LOGGED_IN)))
                self._logged_in = True
                logger.info("WhatsApp logged in.")
            except TimeoutException:
                callback("", "", False, "WhatsApp login timed out")
                return

        name_col   = next((c for c in df.columns if c.lower() == "name"), None)
        number_col = next((c for c in df.columns if c.lower() == "number"), None)
        total = len(df)
        logger.info("Starting send loop: %d contacts | image=%s | use_number=%s",
                    total, image_path or "none", use_number)

        ready_image = None
        if image_path and os.path.exists(image_path):
            logger.info("Preparing image once for all contacts: %s", image_path)
            ready_image = _prepare_image(image_path)
        else:
            logger.info("No image file provided or file does not exist — text only.")

        for i, (_, row) in enumerate(df.iterrows(), 1):
            name       = str(row[name_col]).strip() if name_col else ""
            first_name = _extract_first_name(name) if name else "Friend"
            personalized = message_template.format(first_name=first_name)

            logger.info("========== [%d/%d] Contact: '%s' (first_name='%s') ==========",
                        i, total, name or "unknown", first_name)

            if use_number and number_col:
                raw_number = str(row[number_col]).strip()
                number = _normalize_phone(raw_number)
                logger.info("[%s] Number from sheet: '%s' → normalized: '%s'", first_name, raw_number, number)
                logger.info("[%s] Navigating to https://web.whatsapp.com/send?phone=%s ...", first_name, number)
                self.driver.get(f"https://web.whatsapp.com/send?phone={number}")
                logger.info("[%s] Page loaded. Waiting 4s for chat to initialize...", first_name)
                time.sleep(4)
                try:
                    if ready_image:
                        logger.info("[%s] Sending image first...", first_name)
                        self._send_image_only(first_name, ready_image)
                        logger.info("[%s] Image sent. Now sending text...", first_name)
                    else:
                        logger.info("[%s] No image — sending text only.", first_name)
                    self._send_text(first_name, personalized)
                    logger.info("[%s] ✓ ALL DONE via number %s.", first_name, number)
                    callback(first_name, number, True, "Sent")
                except Exception as e:
                    logger.error("[%s] ✗ FAILED via number %s: %s", first_name, number, e)
                    callback(first_name, number, False, str(e))
            elif name:
                logger.info("[%s] Using name-search flow.", first_name)
                success, msg = self._process_contact(name, personalized, image_path)
                callback(first_name, "", success, msg)
            else:
                logger.warning("Row %d: no name and no number — skipping.", i)
                callback("", "", False, "No usable identifier in row")
