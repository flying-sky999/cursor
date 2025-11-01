# -*- coding: utf-8 -*-

"""
Pika (web) smoke automation test - v1 (derived from the Runway Gen-4 v12 workflow)
- Load task sheet -> open https://pika.art -> ensure studio workspace
- Optionally upload a reference clip if UI exposes an upload action
- Auto-fill prompt, trigger a single generation attempt after a stability dwell
- Poll for render completion and download the result using Method A (fixed selectors/text only)

Assumptions:
- The persistent browser profile already holds a signed-in Pika session
- The studio UI provides a discoverable Generate/Create/Make button and a download control
- Playwright (sync API) and pandas are installed in the environment
"""

import os
import sys
import time
import re
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd
from playwright.sync_api import Locator, Page, sync_playwright


# ===== Paths & profile configuration =====
VIDEO_DIR = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/source"
SHEET_PATH = r"/Users/helensliang/important/paper-data-ppt/InstructBench/InstructBench.xlsx"
DOWNLOAD_DIR = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/output"
USER_DATA_DIR = str(Path.home() / "pika_playwright_profile")

PIKA_HOME_URL = "https://pika.art/"
PIKA_APP_URLS = [
    "https://pika.art/app",
    "https://pika.art/dashboard",
    "https://pika.art/text-to-video",
]

DEFAULT_JOB_LABEL = datetime.now().strftime("pika_%Y%m%d_%H%M%S")

PIKA_LOGIN_URL = "https://pika.art/login"
PIKA_EMAIL = os.environ.get("PIKA_EMAIL", "mjanwfdj7323@outlook.com")
PIKA_PASSWORD = os.environ.get("PIKA_PASSWORD", "Yguyl51168.")


# ===== Timing / timeouts =====
NAV_TIMEOUT = 120_000
ACTION_TIMEOUT = 60_000
UPLOAD_PREP_TIMEOUT = 30 * 60
READY_DWELL_SEC = 8
MIN_RENDER_WAIT_SEC = 240
JOB_TIMEOUT_SEC = 45 * 60
POLL_INTERVAL_SEC = 3
A_STABLE_SEC = 2
CLICK_COOLDOWN_SEC = 6


# ===== Generic selectors =====
BTN_REGEX = r"(Generate|Create|Make|Render|Submit|Launch)"
SELECTORS = {
    "launch_app": "a:has-text('Launch'), a:has-text('Launch App'), button:has-text('Launch App'), button:has-text('Open Studio')",
    "new_video": "button:has-text('Create'), button:has-text('Start new video'), [role='button']:has-text('New video')",
    "upload_buttons": "button:has-text('Upload'), button:has-text('Upload reference'), button:has-text('Upload video')",
    "file_input": "input[type='file']",
    "prompt_candidates": [
        "textarea[placeholder*='Describe']",
        "textarea[placeholder*='Prompt']",
        "textarea:not([disabled])",
        "div[contenteditable='true']",
        "[role='textbox']",
        "textarea",
        "input[type='text']",
    ],
    "processing_only": "text=/Generating|Rendering|Queued|Processing|Preparing/i",
    "complete_badge": "text=/Ready|Completed|Done|Generated/i",
    "download_banner": "text=/Download|\\u4fdd\\u5b58|\\u5bfc\\u51fa|Export/i",
    "cookie_accept": "button:has-text('Accept'), button:has-text('Agree'), button:has-text('Allow'), button[data-testid='cookies-accept']",
    "dismiss_toast": "button[aria-label='Close'], button:has-text('Dismiss')",
    "login_trigger": "a:has-text('Log in'), a:has-text('Sign in'), button:has-text('Log in'), button:has-text('Sign in')",
    "email_input": "input[name='email'], input[type='email']",
    "password_input": "input[name='password'], input[type='password']",
    "login_submit": "button:has-text('Continue'), button:has-text('Log in'), button:has-text('Sign in')",
    "account_badge": "[data-testid='navbar-user-menu'], button:has-text('Account'), img[alt*='avatar']",
    "pikaswap_prompt": "#promptText",
    "pikaswap_video_input": "#modify-region-video",
    "pikaswap_video_label": "label[for='modify-region-video']",
    "pikaswap_start_button": "button:has-text('????'), button:has-text('Start editing'), [role='button']:has-text('Start editing')",
}


# ===== Method A: fixed classes / attributes only =====
A_MAIN = [
    "button[data-testid='download-button']",
    "button[data-icon='download']",
    "button[class*='download'], a[class*='download']",
    "button:has-text('Download'), a:has-text('Download')",
    "button:has-text('Export'), a:has-text('Export')",
    "button:has-text('\\u4fdd\\u5b58'), a:has-text('\\u4fdd\\u5b58')",
]

A_CHEV = [
    "button[aria-haspopup='menu']",
    "button[data-testid='download-menu']",
    "button[class*='caret'], button[class*='chevron'], button:has([data-icon='chevron-down'])",
]


DL_TEXT_ITEMS = [
    "Download MP4",
    "Download GIF",
    "Download",
    "Download video",
    "Export",
    "\u4fdd\u5b58",
    "\u5bfc\u51fa",
]

DL_MENU_REGEX = re.compile(r"(download( mp4| gif| video)?|save|mp4|gif|export|\u5bfc\u51fa|\u4e0b\u8f7d|\u4fdd\u5b58)", re.I)


# ===== Utility helpers =====
def human_sleep(a: float = 0.5, b: float = 1.6) -> None:
    time.sleep(random.uniform(a, b))


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def load_tasks(sheet: str, video_dir: str) -> List[dict]:
    sheet_path = Path(sheet)
    if not sheet_path.exists():
        print(f"[ERROR] Task sheet not found: {sheet}")
        sys.exit(1)

    df = pd.read_excel(sheet_path) if sheet_path.suffix.lower() != ".csv" else pd.read_csv(sheet_path)
    required = {"source_video_path", "instruction"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing required columns {required}; actual columns: {list(df.columns)}")

    tasks: List[dict] = []
    missing_files = 0
    for _, row in df.iterrows():
        src = str(row["source_video_path"]).strip()
        if not src or src.lower() == "nan":
            continue
        filename = Path(src).name
        file_path = Path(video_dir) / filename
        if not file_path.exists():
            print(f"[WARN] Video not found locally: {file_path}")
            missing_files += 1
            continue
        tasks.append(
            {
                "file_path": str(file_path),
                "filename": filename,
                "prompt": str(row["instruction"]).strip(),
            }
        )

    if missing_files:
        print(f"[INFO] Skipped {missing_files} entries due to missing files.")
    return tasks


def safe_goto(page: Page, url: str, attempts: int = 3) -> bool:
    wait_states = ["domcontentloaded", "load", "networkidle"]
    for attempt in range(1, attempts + 1):
        state = wait_states[min(attempt - 1, len(wait_states) - 1)]
        try:
            page.goto(url, wait_until=state, timeout=NAV_TIMEOUT)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            return True
        except Exception as exc:
            print(f"[NAV] goto failed {attempt}/{attempts}: {exc}")
            time.sleep(attempt)
    return False


def accept_cookies(page: Page) -> None:
    try:
        if page.is_visible(SELECTORS["cookie_accept"], timeout=1_500):
            page.click(SELECTORS["cookie_accept"])
            print("[STEP] Accepted cookie banner.")
    except Exception:
        pass


def dismiss_toasts(page: Page) -> None:
    try:
        loc = page.locator(SELECTORS["dismiss_toast"])
        if loc.count():
            for idx in range(loc.count()):
                try:
                    el = loc.nth(idx)
                    if el.is_visible():
                        el.click()
                        time.sleep(0.1)
                except Exception:
                    pass
    except Exception:
        pass


def is_logged_in(page: Page) -> bool:
    try:
        if page.is_visible(SELECTORS["account_badge"], timeout=1_500):
            return True
    except Exception:
        pass

    try:
        if not page.is_visible(SELECTORS["login_trigger"], timeout=1_500):
            # Heuristic: absence of login button + presence of creation controls implies logged in
            if page.is_visible(SELECTORS["new_video"], timeout=1_000):
                return True
    except Exception:
        pass

    return False


def perform_login(page: Page) -> bool:
    if not PIKA_EMAIL or not PIKA_PASSWORD:
        print("[ERROR] Missing PIKA_EMAIL or PIKA_PASSWORD configuration.")
        return False

    try:
        if not page.is_visible(SELECTORS["email_input"], timeout=5_000):
            print("[ERROR] Login form not detected on the page.")
            return False
    except Exception as exc:
        print("[ERROR] Unexpected error locating login form:", exc)
        return False

    try:
        page.fill(SELECTORS["email_input"], PIKA_EMAIL, timeout=ACTION_TIMEOUT)
    except Exception:
        try:
            email_box = page.locator(SELECTORS["email_input"]).first
            email_box.click(timeout=ACTION_TIMEOUT)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(PIKA_EMAIL, delay=18)
        except Exception as exc:
            print("[ERROR] Unable to fill email field:", exc)
            return False

    try:
        page.fill(SELECTORS["password_input"], PIKA_PASSWORD, timeout=ACTION_TIMEOUT)
    except Exception:
        try:
            password_box = page.locator(SELECTORS["password_input"]).first
            password_box.click(timeout=ACTION_TIMEOUT)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(PIKA_PASSWORD, delay=18)
        except Exception as exc:
            print("[ERROR] Unable to fill password field:", exc)
            return False

    try:
        if page.is_visible(SELECTORS["login_submit"], timeout=1_500):
            page.click(SELECTORS["login_submit"])
        else:
            page.keyboard.press("Enter")
    except Exception as exc:
        print("[WARN] Login submit interaction encountered an issue:", exc)
        try:
            page.keyboard.press("Enter")
        except Exception:
            pass

    for _ in range(30):
        if is_logged_in(page):
            print("[STEP] Login successful.")
            return True
        time.sleep(1.5)

    print("[ERROR] Login attempt timed out. Please verify credentials or UI changes.")
    return False


def ensure_logged_in(page: Page) -> bool:
    if is_logged_in(page):
        print("[STEP] Detected existing authenticated session.")
        return True

    try:
        if page.is_visible(SELECTORS["login_trigger"], timeout=3_000):
            page.click(SELECTORS["login_trigger"])
            human_sleep()
    except Exception as exc:
        print("[WARN] Unable to trigger login dialog via navbar:", exc)

    if not page.is_visible(SELECTORS["email_input"], timeout=5_000):
        if not safe_goto(page, PIKA_LOGIN_URL):
            print("[ERROR] Failed to navigate to the login page.")
            return False
        human_sleep(0.8, 1.6)

    if not perform_login(page):
        return False

    # Provide a small buffer for post-login redirects
    human_sleep(1.0, 2.0)
    if not is_logged_in(page):
        print("[WARN] Login did not yield an authenticated state. Re-check UI manually.")
        return False

    return True


def ensure_studio_ready(page: Page) -> bool:
    """Make sure the script is inside the Pika studio workspace."""

    accept_cookies(page)

    for target_url in PIKA_APP_URLS:
        if page.url.startswith(target_url):
            return True

    try:
        if page.is_visible(SELECTORS["launch_app"], timeout=5_000):
            page.click(SELECTORS["launch_app"])
            human_sleep(0.8, 1.6)
    except Exception as exc:
        print(f"[WARN] Launch App click issue: {exc}")

    for candidate in PIKA_APP_URLS:
        if safe_goto(page, candidate):
            human_sleep(1.0, 2.0)
            if page.url.startswith(candidate):
                print(f"[STEP] Entered studio workspace: {candidate}")
                return True

    print("[ERROR] Unable to enter Pika studio workspace. Please confirm login state.")
    return False


def upload_clip(page: Page, file_path: str) -> bool:
    """Attempt to upload a reference video if an upload control is exposed."""

    try:
        with page.expect_file_chooser(timeout=20_000) as chooser:
            page.click(SELECTORS["upload_buttons"])
        chooser.value.set_files(file_path)
        print(f"[STEP] Selected file via chooser: {file_path}")
        return True
    except Exception as exc:
        print("[INFO] File chooser not triggered, fallback to direct input[type=file]:", exc)

    try:
        if page.is_visible(SELECTORS["file_input"], timeout=3_000):
            page.set_input_files(SELECTORS["file_input"], file_path)
            print(f"[STEP] Selected file via input[type=file]: {file_path}")
            return True
        inputs = page.query_selector_all("input[type='file']")
        if inputs:
            inputs[0].set_input_files(file_path)
            print(f"[STEP] Selected file via fallback input[type=file]: {file_path}")
            return True
    except Exception as exc:
        print("[WARN] Failed to assign file chooser:", exc)

    print("[INFO] Upload action skipped (control may not be required).")
    return False


def run_pikaswap_flow(page: Page, prompt_text: Optional[str], video_path: Optional[str]) -> bool:
    """Fill prompt, upload swap video, and click the Start Editing control inside the PikaSwap UI."""

    success = True

    if prompt_text:
        try:
            page.fill(SELECTORS["pikaswap_prompt"], prompt_text, timeout=ACTION_TIMEOUT)
            print("[STEP] Filled PikaSwap prompt textarea.")
        except Exception:
            try:
                prompt_box = page.locator(SELECTORS["pikaswap_prompt"]).first
                prompt_box.click(timeout=ACTION_TIMEOUT)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(prompt_text, delay=16)
                print("[STEP] Typed PikaSwap prompt via keyboard fallback.")
            except Exception as exc:
                print("[WARN] Unable to populate PikaSwap prompt:", exc)
                success = False

    if video_path:
        video_file = Path(video_path)
        if not video_file.exists():
            print(f"[WARN] PikaSwap video missing locally: {video_path}")
            success = False
        else:
            try:
                page.set_input_files(SELECTORS["pikaswap_video_input"], str(video_file))
                print(f"[STEP] Assigned video to PikaSwap input: {video_file}")
            except Exception as exc:
                print("[WARN] Direct set_input_files failed, attempting label click:", exc)
                try:
                    with page.expect_file_chooser(timeout=15_000) as chooser:
                        page.click(SELECTORS["pikaswap_video_label"])
                    chooser.value.set_files(str(video_file))
                    print(f"[STEP] Uploaded video via label fallback: {video_file}")
                except Exception as exc2:
                    print("[ERROR] Unable to attach video for PikaSwap:", exc2)
                    success = False

    # Try to click the Start Editing button if it exists.
    start_selectors = [
        SELECTORS["pikaswap_start_button"],
        "button:has-text('????')",
        "button:has-text('Start editing')",
        "[role='button']:has-text('Start editing')",
    ]

    clicked = False
    for sel in start_selectors:
        try:
            if page.is_visible(sel, timeout=1_200):
                page.click(sel)
                clicked = True
                print("[STEP] Triggered PikaSwap start/edit button.")
                break
        except Exception:
            continue

    if not clicked:
        print("[WARN] Could not locate a visible 'Start editing' control. Please verify the selector.")
        success = False

    return success


def find_prompt_input(page: Page) -> Optional[str]:
    for sel in SELECTORS["prompt_candidates"]:
        try:
            if page.is_visible(sel, timeout=800):
                return sel
        except Exception:
            pass
    return None


def set_prompt(page: Page, text: str) -> bool:
    selector = find_prompt_input(page)
    if selector:
        try:
            page.fill(selector, text, timeout=ACTION_TIMEOUT)
            return True
        except Exception:
            try:
                locator = page.locator(selector).first
                locator.click(timeout=ACTION_TIMEOUT)
                try:
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                except Exception:
                    pass
                page.keyboard.type(text, delay=18)
                return True
            except Exception:
                pass

    try:
        locator = page.locator("textarea").first
        locator.click(timeout=ACTION_TIMEOUT)
        page.keyboard.type(text, delay=20)
        return True
    except Exception:
        return False


def get_primary_generate_button(page: Page) -> Optional[Locator]:
    best: Optional[Locator] = None
    max_area = -1
    frames = [page, *page.frames]
    for frame in frames:
        try:
            buttons = frame.get_by_role("button", name=re.compile(BTN_REGEX, re.I))
            count = buttons.count()
            if count <= 0:
                continue
            for idx in range(count):
                candidate = buttons.nth(idx)
                try:
                    if not candidate.is_visible():
                        continue
                    box = candidate.bounding_box()
                    area = (box["width"] * box["height"]) if box else 0
                    if area > max_area:
                        max_area = area
                        best = candidate
                except Exception:
                    pass
        except Exception:
            pass
    return best


def gen_button_enabled(btn: Optional[Locator]) -> bool:
    if not btn:
        return False
    try:
        if not btn.is_visible():
            return False
    except Exception:
        pass

    try:
        return not btn.is_disabled()
    except Exception:
        pass

    try:
        return btn.get_attribute("disabled") is None
    except Exception:
        return True


def processing_banner_visible(page: Page) -> bool:
    try:
        return page.is_visible(SELECTORS["processing_only"], timeout=800)
    except Exception:
        return False


def wait_generate_ready_then_click_once(page: Page) -> bool:
    start = time.time()
    first_ready: Optional[float] = None
    clicked = False
    while time.time() - start < UPLOAD_PREP_TIMEOUT:
        btn = get_primary_generate_button(page)
        ready = bool(btn and gen_button_enabled(btn) and not processing_banner_visible(page))
        now = time.time()

        if ready:
            if first_ready is None:
                first_ready = now
                print(f"[STEP] Generate button ready, waiting {READY_DWELL_SEC}s for stability...")
            if (now - first_ready) >= READY_DWELL_SEC and not clicked:
                try:
                    btn.scroll_into_view_if_needed(timeout=2_000)
                except Exception:
                    pass
                human_sleep(0.3, 0.8)
                try:
                    btn.click(timeout=5_000)
                    clicked = True
                    print("[STEP] Clicked Generate once.")
                    time.sleep(2)
                    return True
                except Exception as exc:
                    print("[WARN] Single click attempt failed (no retry).", exc)
                    return False
        else:
            first_ready = None

        if processing_banner_visible(page):
            print("[INFO] Upload/processing in progress...")

        time.sleep(4)

    return False


def first_visible_in_frames(page: Page, selectors: List[str]) -> Optional[Locator]:
    frames = [page, *page.frames]
    for frame in frames:
        for sel in selectors:
            try:
                locator = frame.locator(sel)
                count = locator.count()
                if count <= 0:
                    continue
                for idx in range(count):
                    element = locator.nth(idx)
                    if element.is_visible():
                        return element
            except Exception:
                pass
    return None


def wait_controls_method_A_only(page: Page, stable_sec: int = A_STABLE_SEC) -> Tuple[Optional[Locator], Optional[Locator]]:
    print("[STEP] (A) Waiting for stable download controls (primary/dropdown)...")
    start = time.time()
    first_seen: Optional[float] = None
    last_signature: Optional[Tuple[str, str]] = None

    while time.time() - start < JOB_TIMEOUT_SEC:
        dismiss_toasts(page)

        main_btn = first_visible_in_frames(page, A_MAIN)
        chev_btn = first_visible_in_frames(page, A_CHEV)

        if main_btn or chev_btn:
            try:
                signature = (
                    page.evaluate("n => n?.outerHTML?.slice(0, 120)", main_btn) if main_btn else "none",
                    page.evaluate("n => n?.outerHTML?.slice(0, 120)", chev_btn) if chev_btn else "none",
                )
            except Exception:
                signature = ("main", "chev")

            now = time.time()
            if signature != last_signature:
                first_seen = now
                last_signature = signature
            if first_seen is None:
                first_seen = now
            if now - first_seen >= stable_sec:
                print("[HIT] Method A located download controls.")
                return main_btn, chev_btn
        else:
            first_seen = None
            last_signature = None

        time.sleep(POLL_INTERVAL_SEC)

    return None, None


def try_download_via_A(page: Page, filename_prefix: str, main_btn: Optional[Locator], chev_btn: Optional[Locator]) -> bool:
    # Attempt primary button first
    if main_btn:
        try:
            print("[TRY] Method A - primary download button...")
            with page.expect_download(timeout=180_000) as download_info:
                try:
                    main_btn.scroll_into_view_if_needed(timeout=2_000)
                except Exception:
                    pass
                main_btn.click(timeout=ACTION_TIMEOUT)
            download = download_info.value
            output_path = Path(DOWNLOAD_DIR) / f"{filename_prefix}_{download.suggested_filename}"
            download.save_as(str(output_path))
            print(f"[OK] Downloaded file: {output_path}")
            return True
        except Exception as exc:
            print(f"[INFO] Primary download button did not trigger: {exc}")
            time.sleep(CLICK_COOLDOWN_SEC)

    # Fallback via dropdown menu
    if chev_btn:
        try:
            print("[TRY] Method A - dropdown download menu...")
            try:
                chev_btn.scroll_into_view_if_needed(timeout=2_000)
            except Exception:
                pass
            chev_btn.click(timeout=ACTION_TIMEOUT)
            time.sleep(0.5)

            target_item: Optional[Locator] = None
            frames = [page, *page.frames]

            for text in DL_TEXT_ITEMS:
                if target_item:
                    break
                for frame in frames:
                    try:
                        loc = frame.get_by_role("menuitem", name=text)
                        if loc.count() and loc.first.is_visible():
                            target_item = loc.first
                            break
                    except Exception:
                        pass

            if not target_item:
                for frame in frames:
                    try:
                        loc = frame.get_by_role("menuitem", name=DL_MENU_REGEX)
                        if loc.count() and loc.first.is_visible():
                            target_item = loc.first
                            break
                    except Exception:
                        pass

            if not target_item:
                target_item = page.locator(
                    "text=/Download|\\u4fdd\\u5b58|\\u5bfc\\u51fa|Export|MP4|GIF/i"
                ).first

            if not target_item:
                print("[WARN] Download option not found within dropdown.")
                time.sleep(CLICK_COOLDOWN_SEC)
                return False

            with page.expect_download(timeout=180_000) as download_info:
                target_item.click(timeout=ACTION_TIMEOUT)
            download = download_info.value
            output_path = Path(DOWNLOAD_DIR) / f"{filename_prefix}_{download.suggested_filename}"
            download.save_as(str(output_path))
            print(f"[OK] Downloaded file: {output_path}")
            return True
        except Exception as exc:
            print(f"[WARN] Dropdown download attempt failed: {exc}")
            time.sleep(CLICK_COOLDOWN_SEC)

    print("[WARN] Method A could not locate a working download control.")
    return False


# ===== Main workflow =====
def main() -> None:
    ensure_dir(DOWNLOAD_DIR)
    tasks = load_tasks(SHEET_PATH, VIDEO_DIR)
    if not tasks:
        print("[ERROR] No runnable tasks found.")
        return

    print(f"[INFO] Pending tasks: {len(tasks)} (Pika smoke test v1)")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            accept_downloads=True,
            ignore_https_errors=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = browser.new_page()
        page.set_viewport_size({"width": 1420, "height": 900})
        page.set_default_timeout(ACTION_TIMEOUT)
        page.set_default_navigation_timeout(NAV_TIMEOUT)

        print("[STEP] Opening Pika home page...")
        if not safe_goto(page, PIKA_HOME_URL):
            print("[ERROR] Unable to reach Pika website.")
            return

        accept_cookies(page)
        time.sleep(2)

        if not ensure_logged_in(page):
            print("[ERROR] Automatic login failed. Please verify credentials and rerun.")
            return

        for idx, task in enumerate(tasks, start=1):
            print(f"\n[JOB {idx}/{len(tasks)}] {task['filename']}")

            if not ensure_studio_ready(page):
                print("[ERROR] Could not enter studio workspace for this task. Skipping.")
                continue

            try:
                if page.is_visible(SELECTORS["new_video"], timeout=5_000):
                    page.click(SELECTORS["new_video"])
                    human_sleep()
            except Exception as exc:
                print("[WARN] Create-new entry misbehaved:", exc)

            upload_clip(page, task["file_path"])

            if not set_prompt(page, task["prompt"]):
                print("[WARN] Prompt auto-fill failed. Please enter manually and press Enter to continue...")
                input()

            print(f"[STEP] Waiting {READY_DWELL_SEC}s of stability before triggering Generate...")
            if not wait_generate_ready_then_click_once(page):
                print("[WARN] Generate action did not fire. Skipping this task.")
                continue

            print(f"[STEP] Generate clicked. Idling for {MIN_RENDER_WAIT_SEC}s to allow rendering...")
            waited = 0
            while waited < MIN_RENDER_WAIT_SEC:
                time.sleep(15)
                waited += 15
                print(f"[INFO] Render quiet wait: {waited}s / {MIN_RENDER_WAIT_SEC}s")

            print("[STEP] Method A loop: detect -> click -> cooldown until success or timeout...")
            cycle_start = time.time()
            downloaded = False

            while time.time() - cycle_start < JOB_TIMEOUT_SEC:
                main_btn, chev_btn = wait_controls_method_A_only(page, A_STABLE_SEC)
                if not main_btn and not chev_btn:
                    print("[WARN] Method A did not find download controls yet. Retrying...")
                    time.sleep(POLL_INTERVAL_SEC)
                    continue

                filename_prefix = f"{Path(task['filename']).stem}_{DEFAULT_JOB_LABEL}"
                if try_download_via_A(page, filename_prefix, main_btn, chev_btn):
                    downloaded = True
                    break

                print(f"[COOLDOWN] Download attempt failed. Cooling down for {CLICK_COOLDOWN_SEC}s...")
                time.sleep(CLICK_COOLDOWN_SEC)

            if not downloaded:
                print("[INFO] Automatic download failed. Please retrieve the asset manually in the UI.")

        print("\n[DONE] All Pika tasks processed.")
        # browser.close()


if __name__ == "__main__":
    main()

