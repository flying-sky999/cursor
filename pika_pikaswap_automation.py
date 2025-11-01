# -*- coding: utf-8 -*-

"""
Pika PikaSwap ????? - ???
???????????
1. ?? https://pika.art/app
2. ?? Pikaswaps ????
3. ????
4. ???????
5. ??????
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
from playwright.sync_api import Page, sync_playwright


# ===== ???? =====
VIDEO_DIR = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/source"
SHEET_PATH = r"/Users/helensliang/important/paper-data-ppt/InstructBench/InstructBench.xlsx"
DOWNLOAD_DIR = r"/Users/helensliang/important/paper-data-ppt/InstructBench/pika/output"
USER_DATA_DIR = str(Path.home() / "pika_playwright_profile")

PIKA_APP_URL = "https://pika.art/app"

# ===== ???? =====
NAV_TIMEOUT = 120_000
ACTION_TIMEOUT = 60_000

# ===== ????? =====
SELECTORS = {
    # Pikaswaps ????
    "pikaswaps_button": "button.flex.flex-col.items-center:has-text('Pikaswaps')",
    
    # ???????????? HTML ???
    "video_upload_div": "div.group.relative.flex.h-15.w-15.shrink-0",
    "video_upload_label": "label[for='modify-region-video']",
    "video_input": "#modify-region-video, input[type='file']",
    
    # Prompt ???
    "prompt_textarea": "#promptText",
    
    # ??????????? SVG ? span ?????
    "generate_button": "button:has(span.fill-dark-background), button span.absolute:has(svg[fill='white'])",
    "generate_button_alt": "button:has(svg[fill='white'])",
}


def human_sleep(a: float = 0.5, b: float = 1.6) -> None:
    """???????????"""
    time.sleep(random.uniform(a, b))


def ensure_dir(path: str) -> None:
    """??????"""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_tasks(sheet: str, video_dir: str) -> List[dict]:
    """? Excel ????????"""
    sheet_path = Path(sheet)
    if not sheet_path.exists():
        print(f"[??] ????????{sheet}")
        sys.exit(1)

    df = pd.read_excel(sheet_path) if sheet_path.suffix.lower() != ".csv" else pd.read_csv(sheet_path)
    required = {"source_video_path", "instruction"}
    if not required.issubset(df.columns):
        raise ValueError(f"?????? {required}?????{list(df.columns)}")

    tasks: List[dict] = []
    missing_files = 0
    
    for _, row in df.iterrows():
        src = str(row["source_video_path"]).strip()
        if not src or src.lower() == "nan":
            continue
        filename = Path(src).name
        file_path = Path(video_dir) / filename
        if not file_path.exists():
            print(f"[??] ????????{file_path}")
            missing_files += 1
            continue
        tasks.append({
            "file_path": str(file_path),
            "filename": filename,
            "prompt": str(row["instruction"]).strip(),
        })

    if missing_files:
        print(f"[??] ?????????? {missing_files} ????")
    
    return tasks


def click_pikaswaps_button(page: Page) -> bool:
    """??1??? Pikaswaps ????"""
    print("[??1] ???? Pikaswaps ????...")
    
    try:
        # ??????????
        page.wait_for_selector(SELECTORS["pikaswaps_button"], timeout=10_000)
        page.click(SELECTORS["pikaswaps_button"], timeout=ACTION_TIMEOUT)
        human_sleep(1.0, 2.0)
        print("? ???? Pikaswaps ??")
        return True
    except Exception as exc:
        print(f"[??] ???? Pikaswaps ???{exc}")
        return False


def upload_video(page: Page, video_path: str) -> bool:
    """??2???????"""
    print(f"[??2] ???????{video_path}")
    
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"[??] ????????{video_path}")
        return False
    
    try:
        # ??1????? file input
        if page.is_visible(SELECTORS["video_input"], timeout=3_000):
            page.set_input_files(SELECTORS["video_input"], str(video_file))
            human_sleep(1.0, 2.0)
            print(f"? ?????????1?")
            return True
    except Exception as exc1:
        print(f"[??] ??1???????2?{exc1}")
        
        try:
            # ??2??????????????
            with page.expect_file_chooser(timeout=15_000) as chooser:
                # ???? div ????
                if page.is_visible(SELECTORS["video_upload_div"], timeout=3_000):
                    page.click(SELECTORS["video_upload_div"])
                elif page.is_visible(SELECTORS["video_upload_label"], timeout=3_000):
                    page.click(SELECTORS["video_upload_label"])
                else:
                    # ???????????
                    page.click("div.group.relative.flex:has(svg)")
            
            chooser.value.set_files(str(video_file))
            human_sleep(1.0, 2.0)
            print(f"? ?????????2?")
            return True
        except Exception as exc2:
            print(f"[??] ???????{exc2}")
            return False


def fill_prompt(page: Page, prompt_text: str) -> bool:
    """??3??????"""
    print(f"[??3] ????????{prompt_text[:50]}...")
    
    try:
        # ?? textarea ??
        page.wait_for_selector(SELECTORS["prompt_textarea"], timeout=10_000)
        
        # ?????
        page.click(SELECTORS["prompt_textarea"], timeout=ACTION_TIMEOUT)
        page.fill(SELECTORS["prompt_textarea"], "", timeout=ACTION_TIMEOUT)
        
        # ?????
        page.fill(SELECTORS["prompt_textarea"], prompt_text, timeout=ACTION_TIMEOUT)
        human_sleep(0.5, 1.0)
        print("? ???????")
        return True
    except Exception as exc:
        print(f"[??] ????????{exc}")
        return False


def click_generate_button(page: Page) -> bool:
    """??4???????"""
    print("[??4] ????????...")
    
    # ??????????
    selectors_to_try = [
        "button:has(span.fill-dark-background)",
        "button:has(span.bg-accent-primary)",
        "button:has(svg[fill='white'])",
        "button span.absolute.left-0.top-0",
        "button:has(span:has(svg[fill='white']))",
    ]
    
    for selector in selectors_to_try:
        try:
            if page.is_visible(selector, timeout=2_000):
                # ??????
                page.locator(selector).first.scroll_into_view_if_needed(timeout=2_000)
                human_sleep(0.3, 0.6)
                
                # ????
                page.click(selector, timeout=ACTION_TIMEOUT)
                human_sleep(1.0, 2.0)
                print(f"? ???????????????{selector}?")
                return True
        except Exception:
            continue
    
    print("[??] ???????????")
    return False


def process_single_task(page: Page, task: dict, task_num: int, total: int) -> bool:
    """??????"""
    print(f"\n{'='*60}")
    print(f"[?? {task_num}/{total}] {task['filename']}")
    print(f"{'='*60}")
    
    # ??1??? Pikaswaps ??
    if not click_pikaswaps_button(page):
        print("[??] ???? Pikaswaps ??")
        return False
    
    # ??2?????
    if not upload_video(page, task["file_path"]):
        print("[??] ??????")
        return False
    
    # ??3??????
    if not fill_prompt(page, task["prompt"]):
        print("[??] ???????")
        return False
    
    # ??4???????
    if not click_generate_button(page):
        print("[??] ????????")
        return False
    
    print(f"? ?? {task_num} ??????????")
    return True


def main() -> None:
    """???"""
    print("="*60)
    print("Pika PikaSwap ????? - ???")
    print("="*60)
    
    # ????????
    ensure_dir(DOWNLOAD_DIR)
    
    # ??????
    tasks = load_tasks(SHEET_PATH, VIDEO_DIR)
    if not tasks:
        print("[??] ??????????")
        return
    
    print(f"\n[??] ???????{len(tasks)}")
    
    # ?????
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
        
        # ??? Pika ??
        print(f"\n[??] ???? {PIKA_APP_URL}...")
        try:
            page.goto(PIKA_APP_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            print("? ??????")
        except Exception as exc:
            print(f"[??] ???????{exc}")
            return
        
        human_sleep(2.0, 3.0)
        
        # ??????
        success_count = 0
        for idx, task in enumerate(tasks, start=1):
            if process_single_task(page, task, idx, len(tasks)):
                success_count += 1
            
            # ??????
            if idx < len(tasks):
                print(f"\n?? 10 ?????????...")
                time.sleep(10)
                
                # ????? app ??
                try:
                    page.goto(PIKA_APP_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
                    human_sleep(2.0, 3.0)
                except Exception as exc:
                    print(f"[??] ???????{exc}")
        
        print(f"\n{'='*60}")
        print(f"????????????{success_count}/{len(tasks)}")
        print(f"{'='*60}")
        
        # ?????????????
        print("\n???????????? Ctrl+C ??...")
        try:
            time.sleep(3600)  # ??1??
        except KeyboardInterrupt:
            print("\n???????...")
        
        browser.close()


if __name__ == "__main__":
    main()
