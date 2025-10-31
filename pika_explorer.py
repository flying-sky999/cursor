# -*- coding: utf-8 -*-
"""
Pika.art ????????
????????????????????????
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_DATA_DIR = str(Path.home() / "pika_playwright_profile")
PIKA_URL = "https://pika.art/"

def explore_page_structure(page):
    """??????"""
    print("\n" + "="*80)
    print("???? Pika.art ????")
    print("="*80)
    
    # 1. ????????
    print("\n?1. ???????")
    upload_selectors = [
        "input[type='file']",
        "button:has-text('Upload')",
        "button:has-text('upload')",
        "[aria-label*='upload' i]",
        "[data-testid*='upload']",
        ".upload-button",
        "button:has-text('Add')",
        "button:has-text('Choose')",
    ]
    
    for sel in upload_selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements:
                print(f"  ? ?? {len(elements)} ????{sel}")
                for i, el in enumerate(elements[:3]):  # ????3?
                    try:
                        visible = el.is_visible()
                        html = page.evaluate("(el) => el.outerHTML.slice(0, 100)", el)
                        print(f"    [{i}] ??={visible}, HTML={html}...")
                    except:
                        pass
        except Exception as e:
            pass
    
    # 2. ????????prompt?
    print("\n?2. Prompt ????")
    prompt_selectors = [
        "textarea",
        "input[type='text']",
        "[contenteditable='true']",
        "[placeholder*='describe' i]",
        "[placeholder*='prompt' i]",
        "[placeholder*='enter' i]",
        "[role='textbox']",
    ]
    
    for sel in prompt_selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements:
                print(f"  ? ?? {len(elements)} ????{sel}")
                for i, el in enumerate(elements[:2]):
                    try:
                        visible = el.is_visible()
                        placeholder = el.get_attribute("placeholder") or ""
                        print(f"    [{i}] ??={visible}, placeholder='{placeholder}'")
                    except:
                        pass
        except:
            pass
    
    # 3. ??????
    print("\n?3. ?????")
    generate_selectors = [
        "button:has-text('Generate')",
        "button:has-text('Create')",
        "button:has-text('Submit')",
        "button:has-text('Render')",
        "[aria-label*='generate' i]",
        "[data-testid*='generate']",
        "button[type='submit']",
    ]
    
    for sel in generate_selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements:
                print(f"  ? ?? {len(elements)} ????{sel}")
                for i, el in enumerate(elements[:3]):
                    try:
                        visible = el.is_visible()
                        text = el.inner_text()
                        disabled = el.is_disabled()
                        print(f"    [{i}] ??={visible}, ??='{text}', ??={disabled}")
                    except:
                        pass
        except:
            pass
    
    # 4. ??????
    print("\n?4. ?????")
    download_selectors = [
        "button:has-text('Download')",
        "a:has-text('Download')",
        "[aria-label*='download' i]",
        "[data-testid*='download']",
        "button[class*='download']",
        "a[download]",
    ]
    
    for sel in download_selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements:
                print(f"  ? ?? {len(elements)} ????{sel}")
                for i, el in enumerate(elements[:3]):
                    try:
                        visible = el.is_visible()
                        text = el.inner_text() if hasattr(el, 'inner_text') else ""
                        print(f"    [{i}] ??={visible}, ??='{text}'")
                    except:
                        pass
        except:
            pass
    
    # 5. ??????
    print("\n?5. ????????10???")
    try:
        buttons = page.query_selector_all("button")
        visible_buttons = []
        for btn in buttons:
            try:
                if btn.is_visible():
                    text = btn.inner_text().strip()
                    if text:
                        visible_buttons.append(text)
            except:
                pass
        
        for i, text in enumerate(visible_buttons[:10]):
            print(f"  [{i}] {text}")
    except:
        pass
    
    # 6. ????????
    print("\n?6. ???????")
    video_selectors = [
        "video",
        ".video-player",
        "[data-testid*='video']",
    ]
    
    for sel in video_selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements:
                print(f"  ? ?? {len(elements)} ????{sel}")
        except:
            pass

def main():
    """???"""
    print("?? Pika.art ??????")
    print("=" * 80)
    
    with sync_playwright() as p:
        # ??????????????
        browser = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=True,
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print(f"\n?? ???? {PIKA_URL}...")
        page.goto(PIKA_URL, wait_until="networkidle", timeout=60000)
        time.sleep(3)
        
        print("\n??  ?????????????? Enter ??...")
        input()
        
        # ????
        print("\n??????")
        explore_page_structure(page)
        
        # ??????
        screenshot_path = "screenshots/pika_homepage.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n?? ????????{screenshot_path}")
        
        # ??????????????
        print("\n\n" + "="*80)
        print("????????...")
        print("="*80)
        
        create_buttons = [
            "button:has-text('Create')",
            "button:has-text('New')",
            "button:has-text('Start')",
            "a:has-text('Create')",
        ]
        
        for sel in create_buttons:
            try:
                if page.is_visible(sel, timeout=2000):
                    print(f"? ???????{sel}")
                    page.click(sel)
                    time.sleep(3)
                    break
            except:
                pass
        
        print("\n??  ?????????? Enter ????...")
        input()
        
        # ??????
        print("\n????????")
        explore_page_structure(page)
        
        # ????????
        screenshot_path = "screenshots/pika_create_page.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n?? ??????????{screenshot_path}")
        
        print("\n\n" + "="*80)
        print("? ????????????????")
        print("?? ??????????????? Ctrl+C ??")
        print("="*80)
        
        # ???????
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n?? ???...")

if __name__ == "__main__":
    main()
