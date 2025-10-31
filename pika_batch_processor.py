# -*- coding: utf-8 -*-
"""
Pika.art ????????? v1.0
???
- ??????
- ???? prompt
- ??????
- ??????
- ?????????

?????
1. ?????????
2. ??? CSV ????? source_video_path ? instruction ??
3. ?????python pika_batch_processor.py
"""

import os
import sys
import time
import re
import random
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ===== ???? =====
# ??????
VIDEO_DIR = r"./test_videos"
# CSV ??????? source_video_path ? instruction ??
SHEET_PATH = r"./pika_tasks.csv"
# ????
DOWNLOAD_DIR = r"./pika_downloads"
# ??????????????
USER_DATA_DIR = str(Path.home() / "pika_playwright_profile")
# Pika.art URL
PIKA_URL = "https://pika.art/"
# ????
DEFAULT_JOB_LABEL = datetime.now().strftime("pika_%Y%m%d_%H%M%S")

# ===== ???? =====
NAV_TIMEOUT = 150_000            # ??????
ACTION_TIMEOUT = 70_000          # ????
UPLOAD_WAIT_SEC = 30             # ???????
RENDER_WAIT_SEC = 180            # ???????3???
MAX_RENDER_WAIT_SEC = 600        # ?????????10???
POLL_INTERVAL_SEC = 5            # ????
STABLE_WAIT_SEC = 3              # ????????
CLICK_COOLDOWN_SEC = 5           # ??????

# ===== ????? =====
SELECTORS = {
    # ?????
    "create_button": [
        "button:has-text('Create')",
        "button:has-text('New')",
        "a:has-text('Create')",
        "[data-testid='create-button']",
    ],
    
    # ????
    "upload_input": "input[type='file']",
    "upload_button": [
        "button:has-text('Upload')",
        "button:has-text('upload')",
        "[aria-label*='upload' i]",
        "button:has-text('Add video')",
        "button:has-text('Choose file')",
    ],
    "upload_area": [
        "[data-testid='upload-area']",
        ".upload-zone",
        "[role='button']:has-text('upload')",
    ],
    
    # Prompt ??
    "prompt_input": [
        "textarea[placeholder*='describe' i]",
        "textarea[placeholder*='prompt' i]",
        "textarea[placeholder*='enter' i]",
        "textarea:not([disabled])",
        "[contenteditable='true']",
        "[role='textbox']",
        "input[type='text'][placeholder*='describe' i]",
    ],
    
    # ????
    "generate_button": [
        "button:has-text('Generate')",
        "button:has-text('Create')",
        "button:has-text('Submit')",
        "[aria-label*='generate' i]",
        "[data-testid='generate-button']",
    ],
    
    # ?????
    "processing": [
        "text=/Uploading|Processing|Rendering|Generating|Queued/i",
        "[role='progressbar']",
        "[data-testid='progress']",
    ],
    
    # ????
    "download_button": [
        "button:has-text('Download')",
        "a:has-text('Download')",
        "[aria-label*='download' i]",
        "[data-testid='download-button']",
        "button[class*='download']",
        "a[download]",
    ],
    
    # ?????
    "download_menu": [
        "text=/Download|download|??|Save|Export/i",
    ],
}

# ===== ???? =====
def human_sleep(a=0.5, b=1.5):
    """???????????"""
    time.sleep(random.uniform(a, b))

def ensure_dir(path):
    """??????"""
    Path(path).mkdir(parents=True, exist_ok=True)

def load_tasks(sheet_path, video_dir):
    """? CSV/Excel ??????"""
    p = Path(sheet_path)
    if not p.exists():
        print(f"? ???????????{sheet_path}")
        sys.exit(1)
    
    # ????
    if p.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p)
    
    # ?????
    required_cols = {"source_video_path", "instruction"}
    if not required_cols.issubset(df.columns):
        print(f"? ???CSV ??????{required_cols}")
        print(f"   ????{list(df.columns)}")
        sys.exit(1)
    
    # ????
    tasks = []
    missing_count = 0
    
    for _, row in df.iterrows():
        src = str(row["source_video_path"]).strip()
        if not src or src.lower() == "nan":
            continue
        
        # ??????
        filename = Path(src).name
        filepath = Path(video_dir) / filename
        
        if not filepath.exists():
            print(f"??  ???????????{filepath}")
            missing_count += 1
            continue
        
        tasks.append({
            "file_path": str(filepath),
            "filename": filename,
            "prompt": str(row["instruction"]).strip(),
        })
    
    if missing_count:
        print(f"??  ??? {missing_count} ????????")
    
    return tasks

def safe_goto(page, url, attempts=3):
    """???????"""
    for i in range(attempts):
        try:
            wait_states = ["domcontentloaded", "load", "networkidle"]
            wait_state = wait_states[i % len(wait_states)]
            
            page.goto(url, wait_until=wait_state, timeout=NAV_TIMEOUT)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            return True
        except Exception as e:
            print(f"??  ???? ({i+1}/{attempts})?{e}")
            if i < attempts - 1:
                time.sleep(i + 1)
    
    return False

def find_visible_element(page, selectors, timeout=2000):
    """????????????????"""
    if isinstance(selectors, str):
        selectors = [selectors]
    
    for selector in selectors:
        try:
            # ??????? frame ???
            for context in [page, *page.frames]:
                try:
                    if context.is_visible(selector, timeout=timeout):
                        return context.locator(selector).first
                except:
                    pass
        except:
            pass
    
    return None

def upload_video(page, file_path):
    """??????"""
    print(f"?? ???????{Path(file_path).name}")
    
    # ??1??? file chooser
    try:
        upload_btn = find_visible_element(page, SELECTORS["upload_button"], timeout=3000)
        if upload_btn:
            print("   ??????????????...")
            with page.expect_file_chooser(timeout=30000) as fc_info:
                upload_btn.click()
            fc_info.value.set_files(file_path)
            print("   ? ??????????")
            return True
    except Exception as e:
        print(f"   ??1???{e}")
    
    # ??2????? input[type=file]
    try:
        file_inputs = page.query_selector_all(SELECTORS["upload_input"])
        if file_inputs:
            print(f"   ?? {len(file_inputs)} ????????????...")
            file_inputs[0].set_input_files(file_path)
            print("   ? ????? input ??")
            return True
    except Exception as e:
        print(f"   ??2???{e}")
    
    # ??3??????????
    try:
        upload_area = find_visible_element(page, SELECTORS["upload_area"], timeout=3000)
        if upload_area:
            print("   ?????????...")
            with page.expect_file_chooser(timeout=30000) as fc_info:
                upload_area.click()
            fc_info.value.set_files(file_path)
            print("   ? ???????????")
            return True
    except Exception as e:
        print(f"   ??3???{e}")
    
    print("   ? ??????????")
    return False

def set_prompt(page, text):
    """?? prompt ??"""
    print(f"??  ?? prompt?{text[:50]}...")
    
    prompt_input = find_visible_element(page, SELECTORS["prompt_input"], timeout=5000)
    
    if not prompt_input:
        print("   ??  ??? prompt ???")
        return False
    
    try:
        # ??1??? fill
        prompt_input.fill(text, timeout=ACTION_TIMEOUT)
        print("   ? Prompt ????fill?")
        return True
    except:
        pass
    
    try:
        # ??2??? + ????
        prompt_input.click(timeout=ACTION_TIMEOUT)
        human_sleep(0.3, 0.6)
        
        # ??????
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        human_sleep(0.2, 0.4)
        
        # ????
        page.keyboard.type(text, delay=random.randint(20, 50))
        print("   ? Prompt ????keyboard?")
        return True
    except Exception as e:
        print(f"   ? ?? prompt ???{e}")
        return False

def wait_element_ready(page, selectors, check_enabled=True, timeout_sec=60):
    """?????????????"""
    start = time.time()
    first_seen = None
    
    while time.time() - start < timeout_sec:
        element = find_visible_element(page, selectors, timeout=1000)
        
        if element:
            # ??????
            if check_enabled:
                try:
                    is_disabled = element.is_disabled()
                    if is_disabled:
                        first_seen = None
                        time.sleep(1)
                        continue
                except:
                    pass
            
            # ????????
            if first_seen is None:
                first_seen = time.time()
            
            # ???????
            if (time.time() - first_seen) >= STABLE_WAIT_SEC:
                return element
        else:
            first_seen = None
        
        time.sleep(1)
    
    return None

def is_processing(page):
    """????????"""
    try:
        return page.is_visible("|".join(SELECTORS["processing"]), timeout=1000)
    except:
        return False

def click_generate(page):
    """??????"""
    print("?? ????????...")
    
    # ??????
    print("   ????????...")
    time.sleep(UPLOAD_WAIT_SEC)
    
    # ????????
    start = time.time()
    while time.time() - start < 120:
        if is_processing(page):
            print("   ? ?????...")
            time.sleep(5)
            continue
        
        generate_btn = wait_element_ready(
            page, 
            SELECTORS["generate_button"],
            check_enabled=True,
            timeout_sec=10
        )
        
        if generate_btn:
            try:
                # ?????
                generate_btn.scroll_into_view_if_needed(timeout=2000)
                human_sleep(0.5, 1.0)
                
                # ??
                generate_btn.click(timeout=10000)
                print("   ? ???????")
                return True
            except Exception as e:
                print(f"   ??  ?????{e}")
                time.sleep(CLICK_COOLDOWN_SEC)
        else:
            print("   ? ????????...")
            time.sleep(2)
    
    print("   ? ??????")
    return False

def wait_for_render(page):
    """??????"""
    print(f"? ??????????? {RENDER_WAIT_SEC}s?...")
    
    # ????
    waited = 0
    while waited < RENDER_WAIT_SEC:
        time.sleep(10)
        waited += 10
        print(f"   ???... {waited}s / {RENDER_WAIT_SEC}s")
    
    # ??????
    print("   ??????...")
    start = time.time()
    while time.time() - start < MAX_RENDER_WAIT_SEC - RENDER_WAIT_SEC:
        if not is_processing(page):
            print("   ? ???????")
            return True
        
        print(f"   ? ?????...")
        time.sleep(POLL_INTERVAL_SEC)
    
    print("   ??  ????????")
    return True  # ??????

def download_video(page, filename_prefix):
    """???????"""
    print("?? ??????...")
    
    # ????????
    start = time.time()
    while time.time() - start < 120:
        download_btn = find_visible_element(
            page,
            SELECTORS["download_button"],
            timeout=3000
        )
        
        if download_btn:
            try:
                # ?????
                download_btn.scroll_into_view_if_needed(timeout=2000)
                human_sleep(0.5, 1.0)
                
                # ????
                print("   ??????...")
                with page.expect_download(timeout=240_000) as download_info:
                    download_btn.click(timeout=10000)
                
                # ????
                download = download_info.value
                output_path = Path(DOWNLOAD_DIR) / f"{filename_prefix}_{download.suggested_filename}"
                download.save_as(str(output_path))
                
                print(f"   ? ????{output_path}")
                return True
                
            except PlaywrightTimeout:
                print("   ??  ?????????????...")
                
                # ????????
                try:
                    download_btn.click(timeout=5000)
                    human_sleep(0.5, 1.0)
                    
                    # ?????
                    menu_item = find_visible_element(
                        page,
                        SELECTORS["download_menu"],
                        timeout=3000
                    )
                    
                    if menu_item:
                        with page.expect_download(timeout=240_000) as download_info:
                            menu_item.click(timeout=10000)
                        
                        download = download_info.value
                        output_path = Path(DOWNLOAD_DIR) / f"{filename_prefix}_{download.suggested_filename}"
                        download.save_as(str(output_path))
                        
                        print(f"   ? ????????{output_path}")
                        return True
                except Exception as e:
                    print(f"   ? ?????{e}")
                
            except Exception as e:
                print(f"   ? ?????{e}")
            
            time.sleep(CLICK_COOLDOWN_SEC)
        else:
            print("   ? ??????...")
            time.sleep(POLL_INTERVAL_SEC)
    
    print("   ??  ????????????")
    return False

# ===== ??? =====
def main():
    """???"""
    print("=" * 80)
    print("?? Pika.art ????????? v1.0")
    print("=" * 80)
    
    # ??????
    ensure_dir(DOWNLOAD_DIR)
    ensure_dir(VIDEO_DIR)
    
    # ????
    tasks = load_tasks(SHEET_PATH, VIDEO_DIR)
    if not tasks:
        print("? ????????")
        return
    
    print(f"\n? ??? {len(tasks)} ???")
    print(f"?? ?????{VIDEO_DIR}")
    print(f"?? ?????{DOWNLOAD_DIR}")
    print(f"?? ?????{SHEET_PATH}")
    print("\n" + "=" * 80)
    
    # ?????
    with sync_playwright() as p:
        print("\n?? ?????...")
        browser = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            accept_downloads=True,
            ignore_https_errors=True,
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(ACTION_TIMEOUT)
        page.set_default_navigation_timeout(NAV_TIMEOUT)
        
        # ?? Pika.art
        print(f"?? ?? {PIKA_URL}...")
        if not safe_goto(page, PIKA_URL):
            print("? ???? Pika.art")
            return
        
        time.sleep(3)
        
        # ??????
        print("\n??  ?????????? Enter ??...")
        input()
        
        # ??????
        for i, task in enumerate(tasks, 1):
            print(f"\n{'=' * 80}")
            print(f"?? ?? {i}/{len(tasks)}")
            print(f"   ???{task['filename']}")
            print(f"   Prompt?{task['prompt'][:60]}...")
            print("=" * 80)
            
            try:
                # ????
                print("\n?? ????...")
                safe_goto(page, PIKA_URL)
                human_sleep(1, 2)
                
                # ????????????
                create_btn = find_visible_element(page, SELECTORS["create_button"], timeout=3000)
                if create_btn:
                    print("   ??????...")
                    create_btn.click()
                    human_sleep(1, 2)
                
                # ????
                if not upload_video(page, task["file_path"]):
                    print("? ??????????")
                    continue
                
                human_sleep(1, 2)
                
                # ?? prompt
                if not set_prompt(page, task["prompt"]):
                    print("??  Prompt ??????????")
                    print("??  ?????? Enter ??...")
                    input()
                
                human_sleep(1, 2)
                
                # ????
                if not click_generate(page):
                    print("? ??????????")
                    continue
                
                # ????
                wait_for_render(page)
                
                # ????
                filename_prefix = f"{Path(task['filename']).stem}_{DEFAULT_JOB_LABEL}"
                download_video(page, filename_prefix)
                
                print(f"\n? ?? {i} ??")
                
            except KeyboardInterrupt:
                print("\n\n??  ????")
                break
            except Exception as e:
                print(f"\n? ?? {i} ???{e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 80)
        print("?? ?????????")
        print("=" * 80)
        print("\n?? ????????????? Enter ??...")
        input()

if __name__ == "__main__":
    main()
