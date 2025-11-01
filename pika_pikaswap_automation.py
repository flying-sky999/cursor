# -*- coding: utf-8 -*-

"""
Pika PikaSwap Automation Script - Coordinate Click Version

Uses coordinate-based clicking for reliable video upload
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
from playwright.sync_api import Page, sync_playwright


# ===== Path Configuration =====
VIDEO_DIR = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/source"
SHEET_PATH = r"/Users/helensliang/important/paper-data-ppt/InstructBench/InstructBench.xlsx"
DOWNLOAD_DIR = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/output"
USER_DATA_DIR = str(Path.home() / "pika_playwright_profile")

PIKA_APP_URL = "https://pika.art/app"

# ===== Timeout Settings =====
NAV_TIMEOUT = 120_000
ACTION_TIMEOUT = 60_000


def human_sleep(a: float = 0.5, b: float = 1.6) -> None:
    """Random sleep to simulate human behavior"""
    time.sleep(random.uniform(a, b))


def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_debug_screenshot(page: Page, name: str) -> None:
    """Save a screenshot for debugging purposes"""
    try:
        screenshot_dir = Path(DOWNLOAD_DIR) / "debug_screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"{name}_{timestamp}.png"
        page.screenshot(path=str(screenshot_path))
        print(f"[DEBUG] Screenshot saved: {screenshot_path}")
    except Exception as e:
        print(f"[WARN] Could not save screenshot: {e}")


def load_tasks(sheet: str, video_dir: str) -> List[dict]:
    """Load task list from Excel sheet"""
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
            print(f"[WARN] Video file not found: {file_path}")
            missing_files += 1
            continue
        tasks.append({
            "file_path": str(file_path),
            "filename": filename,
            "prompt": str(row["instruction"]).strip(),
        })

    if missing_files:
        print(f"[INFO] Skipped {missing_files} entries due to missing files.")
    
    return tasks


def click_pikaswaps_button(page: Page) -> bool:
    """Step 1: Click Pikaswaps feature button"""
    print("[STEP 1] Clicking Pikaswaps feature button...")
    
    try:
        # Try using the provided selector
        pikaswaps_selector = "button:has-text('Pikaswaps')"
        page.wait_for_selector(pikaswaps_selector, timeout=10_000)
        page.click(pikaswaps_selector, timeout=ACTION_TIMEOUT)
        print("? Successfully clicked Pikaswaps button")
        
        # Wait for the Pikaswaps interface to load
        print("[INFO] Waiting for Pikaswaps interface to load...")
        human_sleep(3.0, 4.0)
        
        # Wait for form to be present
        try:
            page.wait_for_selector("form", timeout=10_000)
            print("[INFO] Form detected, interface ready")
        except Exception:
            print("[WARN] Form not detected, but continuing...")
        
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to click Pikaswaps button: {exc}")
        return False


def upload_video(page: Page, video_path: str) -> bool:
    """Step 2: Upload video by clicking at fixed coordinates (677, 396)"""
    print(f"[STEP 2] Uploading video: {video_path}")
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] Video file does not exist: {video_path}")
        return False
    
    print(f"[DEBUG] Video file size: {video_file.stat().st_size / (1024*1024):.2f} MB")
    save_debug_screenshot(page, "before_upload")
    
    # Method 1: Click at fixed coordinates (677, 396) - PRIMARY METHOD
    print("\n[METHOD 1] Clicking at fixed coordinates (677, 396)...")
    try:
        # Fixed coordinates for upload button
        upload_x = 677
        upload_y = 396
        
        print(f"[INFO] Clicking at fixed position: ({upload_x}, {upload_y})")
        
        # Wait a moment for UI to be ready
        human_sleep(1.0, 1.5)
        
        # Click at the fixed coordinates and expect file chooser
        with page.expect_file_chooser(timeout=15_000) as chooser:
            page.mouse.click(upload_x, upload_y)
        
        # Select the video file from local folder
        chooser.value.set_files(str(video_file))
        print(f"[INFO] File selected: {video_file.name}")
        
        # Wait for upload to process
        human_sleep(3.0, 4.0)
        
        print("? Successfully uploaded video via fixed coordinates (677, 396)")
        save_debug_screenshot(page, "after_upload_success")
        return True
        
    except Exception as exc:
        print(f"[WARN] Fixed coordinate click at (677, 396) failed: {exc}")
    
    # Method 2: Try direct file input
    print("\n[METHOD 2] Trying direct file input...")
    try:
        input_selector = "#modify-region-video"
        if page.locator(input_selector).count() > 0:
            print(f"[TRY] Setting files directly to input")
            page.set_input_files(input_selector, str(video_file), timeout=10_000)
            human_sleep(3.0, 4.0)
            print("? Successfully uploaded video via direct input")
            return True
    except Exception as exc:
        print(f"[WARN] Direct input failed: {exc}")
    
    # Method 3: Try alternative coordinates near (677, 396)
    print("\n[METHOD 3] Trying alternative coordinates...")
    try:
        # Try clicking at slightly different positions around the original point
        alternative_positions = [
            (677, 380),  # Slightly above
            (677, 410),  # Slightly below
            (660, 396),  # Slightly left
            (694, 396),  # Slightly right
            (677, 370),  # More above (icon area)
        ]
        
        for x, y in alternative_positions:
            try:
                print(f"[TRY] Clicking at alternative position: ({x}, {y})")
                with page.expect_file_chooser(timeout=10_000) as chooser:
                    page.mouse.click(x, y)
                
                chooser.value.set_files(str(video_file))
                human_sleep(3.0, 4.0)
                print(f"? Successfully uploaded video at ({x}, {y})")
                return True
            except Exception:
                continue
    except Exception as exc:
        print(f"[WARN] Alternative coordinates failed: {exc}")
    
    # Method 4: Traditional label click
    print("\n[METHOD 4] Traditional label click...")
    try:
        label_selector = "label[for='modify-region-video']"
        with page.expect_file_chooser(timeout=15_000) as chooser:
            page.click(label_selector, timeout=ACTION_TIMEOUT)
        
        chooser.value.set_files(str(video_file))
        human_sleep(3.0, 4.0)
        print("? Successfully uploaded video via label click")
        return True
    except Exception as exc:
        print(f"[WARN] Label click failed: {exc}")
    
    print("\n[ERROR] All upload methods failed")
    save_debug_screenshot(page, "upload_failed")
    return False


def fill_prompt(page: Page, prompt_text: str) -> bool:
    """Step 3: Fill prompt textarea"""
    print(f"[STEP 3] Filling prompt: {prompt_text[:50]}...")
    
    prompt_selector = "#promptText"
    
    try:
        # Wait for textarea
        page.wait_for_selector(prompt_selector, state="visible", timeout=10_000)
        
        # Click to focus
        page.click(prompt_selector, timeout=ACTION_TIMEOUT)
        human_sleep(0.3, 0.6)
        
        # Clear and fill
        page.fill(prompt_selector, "", timeout=ACTION_TIMEOUT)
        page.fill(prompt_selector, prompt_text, timeout=ACTION_TIMEOUT)
        human_sleep(0.5, 1.0)
        
        # Verify
        current_value = page.input_value(prompt_selector)
        if current_value == prompt_text:
            print("? Successfully filled prompt")
            return True
        else:
            print(f"[WARN] Text mismatch: expected {len(prompt_text)} chars, got {len(current_value)}")
            # Still return True if we got something
            return len(current_value) > 0
            
    except Exception as exc:
        print(f"[ERROR] Failed to fill prompt: {exc}")
        return False


def click_generate_button(page: Page) -> bool:
    """Step 4: Click generate button"""
    print("[STEP 4] Clicking generate button...")
    
    # Try multiple selectors
    button_selectors = [
        "button:has(span.absolute.left-0.top-0:has(svg[fill='white']))",
        "button:has(span.bg-accent-primary)",
        "button:has(svg[fill='white'])",
        "button[type='submit']",
        "form button:not([type='button'])",
    ]
    
    for selector in button_selectors:
        try:
            if not page.is_visible(selector, timeout=2_000):
                continue
            
            print(f"[TRY] Clicking button: {selector}")
            button = page.locator(selector).first
            
            # Scroll into view
            button.scroll_into_view_if_needed(timeout=2_000)
            human_sleep(0.5, 1.0)
            
            # Click
            button.click(timeout=ACTION_TIMEOUT)
            human_sleep(2.0, 3.0)
            
            print(f"? Successfully clicked generate button")
            return True
        except Exception as exc:
            print(f"[INFO] Selector {selector} failed: {exc}")
            continue
    
    print("[ERROR] Could not find generate button")
    return False


def process_single_task(page: Page, task: dict, task_num: int, total: int) -> bool:
    """Process a single task"""
    print(f"\n{'='*60}")
    print(f"[TASK {task_num}/{total}] {task['filename']}")
    print(f"{'='*60}")
    
    # Step 1: Click Pikaswaps
    if not click_pikaswaps_button(page):
        print("[FAILED] Could not enter Pikaswaps")
        return False
    
    # Step 2: Upload video
    if not upload_video(page, task["file_path"]):
        print("[FAILED] Video upload failed")
        return False
    
    # Step 3: Fill prompt
    if not fill_prompt(page, task["prompt"]):
        print("[FAILED] Prompt fill failed")
        return False
    
    # Step 4: Click generate
    if not click_generate_button(page):
        print("[FAILED] Generate button click failed")
        return False
    
    print(f"? Task {task_num} completed successfully")
    return True


def main() -> None:
    """Main function"""
    print("="*60)
    print("Pika PikaSwap Automation - Coordinate Click Version")
    print("="*60)
    
    ensure_dir(DOWNLOAD_DIR)
    
    tasks = load_tasks(SHEET_PATH, VIDEO_DIR)
    if not tasks:
        print("[ERROR] No tasks found")
        return
    
    print(f"\n[INFO] Tasks to process: {len(tasks)}")
    
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
        
        print(f"\n[NAV] Opening {PIKA_APP_URL}...")
        try:
            page.goto(PIKA_APP_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            print("? Page loaded")
        except Exception as exc:
            print(f"[ERROR] Failed to load page: {exc}")
            return
        
        human_sleep(2.0, 3.0)
        
        # Process tasks
        success_count = 0
        for idx, task in enumerate(tasks, start=1):
            if process_single_task(page, task, idx, len(tasks)):
                success_count += 1
            
            # Wait between tasks
            if idx < len(tasks):
                print(f"\nWaiting 10 seconds before next task...")
                time.sleep(10)
                
                # Re-navigate
                try:
                    page.goto(PIKA_APP_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
                    human_sleep(2.0, 3.0)
                except Exception as exc:
                    print(f"[WARN] Re-navigation failed: {exc}")
        
        print(f"\n{'='*60}")
        print(f"All tasks processed! Success: {success_count}/{len(tasks)}")
        print(f"{'='*60}")
        
        print("\nBrowser will remain open. Press Ctrl+C to exit...")
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            print("\nClosing...")
        
        browser.close()


if __name__ == "__main__":
    main()
