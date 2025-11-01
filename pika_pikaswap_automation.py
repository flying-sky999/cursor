# -*- coding: utf-8 -*-

"""
Pika PikaSwap Automation Script - Simplified Version

Strictly follows these steps:
1. Navigate to https://pika.art/app
2. Click Pikaswaps feature button
3. Upload video by clicking label element (body > main > div > div.sticky.bottom-0 ... > label)
4. Fill prompt text in textarea#promptText
5. Click generate button (button with sparkle SVG icon)

Key improvements:
- Uses precise DOM selectors provided by user
- Multiple fallback selectors for robustness
- Proper file upload via label click
- Verification of filled text content
- No login validation (assumes persistent session)
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

# ===== Selector Configuration =====
SELECTORS = {
    # Pikaswaps feature button
    "pikaswaps_button": "button.flex.flex-col.items-center:has-text('Pikaswaps')",
    
    # Video upload label (more precise selector based on DOM structure)
    "video_upload_label": "body > main > div > div.sticky.bottom-0 label, label[for='modify-region-video']",
    "video_upload_label_simple": "form label",
    "video_input": "#modify-region-video, input[type='file']",
    
    # Prompt input field
    "prompt_textarea": "#promptText, textarea[placeholder*='swap']",
    
    # Generate button (look for span with specific SVG)
    "generate_button": "button:has(span.fill-dark-background), button:has(span.bg-accent-primary)",
    "generate_button_span": "span.absolute.left-0.top-0:has(svg[fill='white'])",
}


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
        page.wait_for_selector(SELECTORS["pikaswaps_button"], timeout=10_000)
        page.click(SELECTORS["pikaswaps_button"], timeout=ACTION_TIMEOUT)
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
    """Step 2: Upload video file by clicking the label element"""
    print(f"[STEP 2] Uploading video: {video_path}")
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[ERROR] Video file does not exist: {video_path}")
        return False
    
    print(f"[DEBUG] Video file size: {video_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Save a screenshot before attempting upload
    save_debug_screenshot(page, "before_upload")
    
    # First, let's check what upload elements are available on the page
    print("[DEBUG] Checking available upload elements...")
    try:
        # Check for input[type=file]
        file_inputs = page.locator("input[type='file']").count()
        print(f"[DEBUG] Found {file_inputs} file input(s)")
        
        # Check for labels
        labels = page.locator("label").count()
        print(f"[DEBUG] Found {labels} label(s)")
        
        # Check for form
        forms = page.locator("form").count()
        print(f"[DEBUG] Found {forms} form(s)")
    except Exception as e:
        print(f"[DEBUG] Element check failed: {e}")
    
    # Method 1: Try direct file input first (most reliable)
    print("\n[METHOD 1] Trying direct file input...")
    input_selectors = [
        "#modify-region-video",
        "input[type='file']",
        "input[accept*='video']",
        "form input[type='file']",
    ]
    
    for selector in input_selectors:
        try:
            if page.locator(selector).count() > 0:
                print(f"[TRY] Direct input with selector: {selector}")
                page.set_input_files(selector, str(video_file), timeout=10_000)
                human_sleep(2.0, 3.0)
                print(f"? Successfully uploaded video via direct input: {selector}")
                return True
        except Exception as exc:
            print(f"[INFO] Selector {selector} failed: {exc}")
    
    # Method 2: Click label to trigger file chooser
    print("\n[METHOD 2] Trying to click label elements...")
    label_selectors = [
        "label[for='modify-region-video']",
        "form label",
        "div.relative.mx-auto label",
        "div.flex.flex-col.gap-3 label",
        "label:has(svg)",
        "label:has(div.group.relative.flex)",
    ]
    
    for selector in label_selectors:
        try:
            label_count = page.locator(selector).count()
            if label_count == 0:
                continue
                
            print(f"[TRY] Clicking label: {selector} (found {label_count})")
            
            # Try each matching label
            for idx in range(label_count):
                try:
                    label = page.locator(selector).nth(idx)
                    if not label.is_visible():
                        continue
                    
                    print(f"[TRY] Clicking label #{idx}...")
                    with page.expect_file_chooser(timeout=15_000) as chooser:
                        label.click(timeout=ACTION_TIMEOUT)
                    
                    chooser.value.set_files(str(video_file))
                    human_sleep(2.0, 3.0)
                    print(f"? Successfully uploaded video by clicking label #{idx}")
                    return True
                except Exception as exc:
                    print(f"[INFO] Label #{idx} failed: {exc}")
                    continue
        except Exception as exc:
            print(f"[INFO] Selector {selector} failed: {exc}")
    
    # Method 3: Click the div with upload icon
    print("\n[METHOD 3] Trying to click upload icon div...")
    div_selectors = [
        "div.group.relative.flex.h-15.w-15",
        "div.group.relative.flex:has(svg)",
        "div:has(svg path[stroke='#fff'])",
    ]
    
    for selector in div_selectors:
        try:
            if page.locator(selector).count() > 0:
                print(f"[TRY] Clicking div: {selector}")
                with page.expect_file_chooser(timeout=15_000) as chooser:
                    page.click(selector, timeout=ACTION_TIMEOUT)
                
                chooser.value.set_files(str(video_file))
                human_sleep(2.0, 3.0)
                print(f"? Successfully uploaded video by clicking div")
                return True
        except Exception as exc:
            print(f"[INFO] Selector {selector} failed: {exc}")
    
    # Method 4: JavaScript injection to trigger file input
    print("\n[METHOD 4] Trying JavaScript injection...")
    try:
        js_code = f"""
        (filePath) => {{
            const input = document.querySelector('input[type="file"]') || 
                         document.querySelector('#modify-region-video');
            if (input) {{
                console.log('Found input via JS:', input);
                return true;
            }}
            return false;
        }}
        """
        found = page.evaluate(js_code)
        if found:
            print("[INFO] File input found via JS, trying to set files...")
            page.set_input_files("input[type='file']", str(video_file))
            human_sleep(2.0, 3.0)
            print("? Successfully uploaded video via JavaScript")
            return True
    except Exception as exc:
        print(f"[INFO] JavaScript method failed: {exc}")
    
    print("\n[ERROR] All upload methods exhausted. Cannot upload video.")
    
    # Save screenshot for debugging
    save_debug_screenshot(page, "upload_failed")
    
    # Try to print relevant HTML for debugging
    try:
        print("\n[DEBUG] Dumping form HTML for inspection...")
        form_html = page.locator("form").first.inner_html()
        # Print first 500 chars
        print(f"[DEBUG] Form HTML (first 500 chars):\n{form_html[:500]}")
    except Exception as e:
        print(f"[DEBUG] Could not retrieve form HTML: {e}")
    
    print("\n[HINT] Please check if:")
    print("  1. The Pikaswaps page has fully loaded")
    print("  2. The upload area is visible on screen")
    print("  3. The file input element is present in the DOM")
    print("  4. Check the debug screenshots in: {}/debug_screenshots/".format(DOWNLOAD_DIR))
    
    return False


def fill_prompt(page: Page, prompt_text: str) -> bool:
    """Step 3: Fill prompt text in textarea"""
    print(f"[STEP 3] Filling prompt: {prompt_text[:50]}...")
    
    # Try multiple selectors for the prompt field
    prompt_selectors = [
        SELECTORS["prompt_textarea"],
        "#promptText",
        "textarea[name='promptText']",
        "textarea[placeholder*='swap']",
        "textarea",
    ]
    
    for selector in prompt_selectors:
        try:
            # Wait for textarea to be visible
            if not page.is_visible(selector, timeout=3_000):
                continue
            
            print(f"[TRY] Using selector: {selector}")
            
            # Click to focus
            page.click(selector, timeout=ACTION_TIMEOUT)
            human_sleep(0.3, 0.6)
            
            # Clear existing content
            page.evaluate(f"document.querySelector('{selector}').value = ''")
            
            # Fill new content
            page.fill(selector, prompt_text, timeout=ACTION_TIMEOUT)
            human_sleep(0.5, 1.0)
            
            # Verify content was filled
            current_value = page.input_value(selector)
            if current_value == prompt_text:
                print("? Successfully filled prompt")
                return True
            else:
                print(f"[WARN] Filled text doesn't match. Expected length: {len(prompt_text)}, got: {len(current_value)}")
        except Exception as exc:
            print(f"[INFO] Selector {selector} failed: {exc}")
            continue
    
    print("[ERROR] Failed to fill prompt with all selectors")
    return False


def click_generate_button(page: Page) -> bool:
    """Step 4: Click generate button with the sparkle icon"""
    print("[STEP 4] Clicking generate button...")
    
    # Try multiple possible selectors for the generate button
    button_selectors = [
        # Look for button containing the specific span with SVG
        "button:has(span.absolute.left-0.top-0:has(svg[fill='white']))",
        "button:has(span.fill-dark-background)",
        "button:has(span.bg-accent-primary)",
        # Try finding the button by the SVG icon
        "button:has(svg[fill='white'])",
        "button:has(svg path[d*='M8.90747'])",  # SVG path from the sparkle icon
        # Generic submit/generate buttons
        "button[type='submit']",
        "form button:not([type='button'])",
    ]
    
    for selector in button_selectors:
        try:
            print(f"[TRY] Selector: {selector}")
            
            if not page.is_visible(selector, timeout=2_000):
                continue
            
            # Get the button element
            button = page.locator(selector).first
            
            # Scroll into view
            button.scroll_into_view_if_needed(timeout=2_000)
            human_sleep(0.5, 1.0)
            
            # Click the button
            button.click(timeout=ACTION_TIMEOUT)
            human_sleep(2.0, 3.0)
            
            print(f"\u2713 Successfully clicked generate button (selector: {selector})")
            return True
        except Exception as exc:
            print(f"[INFO] Selector {selector} failed: {exc}")
            continue
    
    # Last attempt: try to find any button near the prompt textarea
    try:
        print("[TRY] Looking for button near prompt textarea...")
        # Find textarea, then look for nearby button
        page.click("form button", timeout=ACTION_TIMEOUT)
        human_sleep(2.0, 3.0)
        print("\u2713 Successfully clicked generate button (form button)")
        return True
    except Exception as exc:
        print(f"[ERROR] All generate button selectors failed: {exc}")
    
    return False


def process_single_task(page: Page, task: dict, task_num: int, total: int) -> bool:
    """Process a single task"""
    print(f"\n{'='*60}")
    print(f"[TASK {task_num}/{total}] {task['filename']}")
    print(f"{'='*60}")
    
    # Step 1: Click Pikaswaps button
    if not click_pikaswaps_button(page):
        print("[FAILED] Could not enter Pikaswaps feature")
        return False
    
    # Step 2: Upload video
    if not upload_video(page, task["file_path"]):
        print("[FAILED] Video upload failed")
        return False
    
    # Step 3: Fill prompt
    if not fill_prompt(page, task["prompt"]):
        print("[FAILED] Prompt fill failed")
        return False
    
    # Step 4: Click generate button
    if not click_generate_button(page):
        print("[FAILED] Could not click generate button")
        return False
    
    print(f"? Task {task_num} completed: Generation request submitted")
    return True


def main() -> None:
    """Main function"""
    print("="*60)
    print("Pika PikaSwap Automation Script - Simplified Version")
    print("="*60)
    
    # Ensure output directory exists
    ensure_dir(DOWNLOAD_DIR)
    
    # Load task list
    tasks = load_tasks(SHEET_PATH, VIDEO_DIR)
    if not tasks:
        print("[ERROR] No executable tasks found")
        return
    
    print(f"\n[INFO] Number of tasks to process: {len(tasks)}")
    
    # Launch browser
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
        
        # Navigate to Pika app
        print(f"\n[NAV] Opening {PIKA_APP_URL}...")
        try:
            page.goto(PIKA_APP_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            print("? Page loaded")
        except Exception as exc:
            print(f"[ERROR] Failed to load page: {exc}")
            return
        
        human_sleep(2.0, 3.0)
        
        # Process each task
        success_count = 0
        for idx, task in enumerate(tasks, start=1):
            if process_single_task(page, task, idx, len(tasks)):
                success_count += 1
            
            # Wait between tasks
            if idx < len(tasks):
                print(f"\nWaiting 10 seconds before processing next task...")
                time.sleep(10)
                
                # Re-navigate to app page
                try:
                    page.goto(PIKA_APP_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
                    human_sleep(2.0, 3.0)
                except Exception as exc:
                    print(f"[WARN] Re-navigation failed: {exc}")
        
        print(f"\n{'='*60}")
        print(f"All tasks processed! Success: {success_count}/{len(tasks)}")
        print(f"{'='*60}")
        
        # Keep browser open to view results
        print("\nBrowser will remain open, press Ctrl+C to exit...")
        try:
            time.sleep(3600)  # Keep open for 1 hour
        except KeyboardInterrupt:
            print("\nClosing browser...")
        
        browser.close()


if __name__ == "__main__":
    main()
